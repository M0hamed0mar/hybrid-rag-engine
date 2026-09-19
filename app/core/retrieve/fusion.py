"""Reciprocal Rank Fusion for combining multiple result sets"""
from typing import List, Tuple
from collections import defaultdict
from app.core.chunk.models import DocumentChunk
from app.utils.logger import logger


class ReciprocalRankFusion:
    """
    Combine ranked results from multiple queries using RRF.
    RRF score = sum(1 / (k + rank)) for each occurrence
    """
    
    def __init__(self, constant_k: int = 60):
        self.constant_k = constant_k
    
    def fuse(
        self,
        result_sets: List[List[Tuple[DocumentChunk, float]]]
    ) -> List[Tuple[DocumentChunk, float]]:
        """Fuse multiple ranked result lists"""
        
        if not result_sets:
            return []
        
        if len(result_sets) == 1:
            return result_sets[0]
        
        rrf_scores = defaultdict(float)
        chunk_map = {}
        
        for result_set in result_sets:
            for rank, (chunk, _) in enumerate(result_set, start=1):
                rrf_scores[chunk.id] += 1 / (self.constant_k + rank)
                chunk_map[chunk.id] = chunk
        
        # Sort by RRF score
        fused = sorted(
            [(chunk_map[cid], rrf_scores[cid]) for cid in rrf_scores],
            key=lambda x: x[1],
            reverse=True
        )
        
        logger.info(f"RRF fused {len(result_sets)} sets into {len(fused)} unique chunks")
        return fused