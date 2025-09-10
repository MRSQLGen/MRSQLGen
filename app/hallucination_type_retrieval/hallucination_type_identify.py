import json
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import os


class HallucinationTypeIdentify:
    def __init__(
            self,
            model_name='bert-base-uncased',
            device=None,
            hkb_path="",
            hkb_cache_path=""
    ) -> None:
        super().__init__()
        #
        torch.manual_seed(42)
        np.random.seed(42)

        # self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        # self.encoder = AutoModel.from_pretrained(model_name)
        # self.hidden_size = self.encoder.config.hidden_size


        self.tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
        self.encoder = AutoModel.from_pretrained(model_name, local_files_only=True)
        self.hidden_size = self.encoder.config.hidden_size


        #
        self.cross_attention1 = nn.MultiheadAttention(embed_dim=self.hidden_size, num_heads=8, batch_first=True)
        self.cross_attention2 = nn.MultiheadAttention(embed_dim=self.hidden_size, num_heads=8, batch_first=True)

        #
        def _init_weights(m):
            if isinstance(m, nn.MultiheadAttention):
                nn.init.xavier_uniform_(m.in_proj_weight)
                nn.init.constant_(m.in_proj_bias, 0.)
                nn.init.xavier_uniform_(m.out_proj.weight)
                nn.init.constant_(m.out_proj.bias, 0.)

        self.cross_attention1.apply(_init_weights)
        self.cross_attention2.apply(_init_weights)

        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.encoder.to(self.device)
        self.cross_attention1.to(self.device)
        self.cross_attention2.to(self.device)

        #
        self.encoder.eval()
        self.cross_attention1.eval()
        self.cross_attention2.eval()

        #
        for param in self.encoder.parameters():
            param.requires_grad_(False)
        for param in self.cross_attention1.parameters():
            param.requires_grad_(False)
        for param in self.cross_attention2.parameters():
            param.requires_grad_(False)

        self.hkb_units = []
        self.hkb_path = hkb_path
        self.hkb_cache_path = hkb_cache_path
        # self.hkb_meta_path = hkb_cache_path.replace(".npy", "_meta.json")

        # HKB
        if os.path.exists(hkb_cache_path) and os.path.exists(self.hkb_path):
            self.hkb_units = self._load_hkb_cache()
            print(f"[HKB] Loaded {len(self.hkb_units)} HKB units from cache.")
        else:
            print("[HKB] No HKB cache found. Building HKB...")
            self.build_hkb()

    def _encode(self, text: str) -> torch.Tensor:
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(self.device)
        with torch.no_grad():
            outputs = self.encoder(**inputs).last_hidden_state.squeeze(0)
        return outputs

    def _bidirectional_cross_attention(self, text_embed, sql_embed):
        with torch.no_grad():
            #  [1, seq_len, hidden_dim]
            text_embed = text_embed.unsqueeze(0) if text_embed.dim() == 2 else text_embed
            sql_embed = sql_embed.unsqueeze(0) if sql_embed.dim() == 2 else sql_embed

            t2s, _ = self.cross_attention1(
                query=text_embed,
                key=sql_embed,
                value=sql_embed
            )
            s2t, _ = self.cross_attention2(
                query=sql_embed,
                key=text_embed,
                value=text_embed
            )
            fusion = torch.cat([t2s.squeeze(0), s2t.squeeze(0)], dim=0)
        return fusion.float()  #

    def _save_hkb_cache(self):
        #
        embeddings = np.array([u["embedding"] for u in self.hkb_units], dtype=np.float16)

        #
        np.save(self.hkb_cache_path, embeddings)

    def _load_hkb_cache(self):
        #
        with open(self.hkb_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        embeddings = np.load(self.hkb_cache_path).astype(np.float64)  #
        assert len(meta) == len(embeddings), "Meta-embedding length mismatch!"


        hkb_units = []
        for i, m in enumerate(meta):
            m["embedding"] = embeddings[i].astype(np.float32)
            hkb_units.append(m)
        return hkb_units

    def build_hkb(self):
        self.hkb_units = []
        if not os.path.exists(self.hkb_path):
            raise FileNotFoundError(f"HKB source file not found: {self.hkb_path}")

        with open(self.hkb_path, "r", encoding="utf-8") as r:
            hkb_data = json.load(r)

        print(f"[HKB] Building {len(hkb_data)} units...")
        for unit in hkb_data:
            text_embed = self._encode(unit["question"])
            sql_embed = self._encode(unit["query"])

            fused = self._bidirectional_cross_attention(text_embed, sql_embed)
            mean_embedding = fused.mean(dim=0).detach().cpu().numpy()

            self.hkb_units.append({
                "index": unit["index"],
                "node_type": unit["node_type"],
                "question": unit["question"],
                "query": unit["query"],
                "embedding": mean_embedding
            })

        self._save_hkb_cache()
        print(f"[HKB] Built and saved {len(self.hkb_units)} HKB units.")

    def match(self, text: str, sql: str, top_k):
        #
        text_embed = self._encode(text)
        sql_embed = self._encode(sql)

        #
        fused = self._bidirectional_cross_attention(text_embed, sql_embed)
        global_embedding = fused.mean(dim=0).detach().cpu().numpy().reshape(1, -1)

        #
        hkb_embeds = np.vstack([u["embedding"] for u in self.hkb_units])
        sims = cosine_similarity(global_embedding, hkb_embeds)[0]

        # Top-K
        top_indices = np.argsort(sims)[-top_k:][::-1]
        return [{
            "index": self.hkb_units[idx]["index"],
            "node_type": self.hkb_units[idx]["node_type"],
            "question": self.hkb_units[idx]["question"],
            "query": self.hkb_units[idx]["query"],
            "similarity": float(sims[idx])
        } for idx in top_indices]

    def add_dicts(self, dict1: dict, dict2: dict) -> dict:
        result = {}
        keys = set(dict1.keys()) | set(dict2.keys())  #
        for key in keys:
            result[key] = dict1.get(key, 0.0) + dict2.get(key, 0.0)
        return result

    def top_k_threshold_items(self, d: dict, threshold: float) -> dict:
        #  threshold
        filtered = {key: value for key, value in d.items() if value >= threshold}
        return filtered

    def type_identify_whole(self, text: str, sql: str, top_match_k, threshold_similarity: float):
        # 1. top-k： top-k  matches
        matches = self.match(text, sql, top_match_k)

        merge_similarity = {}
        for match in matches:
            match_similarity = {}
            node_type_temp = match["node_type"]
            similarity_temp = match["similarity"]
            for node, node_bool in node_type_temp.items():
                match_similarity[node] = similarity_temp if node_bool else 0.0
            merge_similarity = self.add_dicts(merge_similarity, match_similarity)

        # node
        for key, value in merge_similarity.items():
            merge_similarity[key] = value/len(matches)

        types_retrieval = self.top_k_threshold_items(merge_similarity, threshold_similarity)

        types_identify = {}
        for key,value in matches[0]["node_type"].items():
            types_identify[key] = True if key in types_retrieval else False
        return types_retrieval, types_identify







