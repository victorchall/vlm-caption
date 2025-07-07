import openai
import numpy as np
from typing import List, Tuple, Dict

_lyrics = """[Intro]
Come wit' it now
Come wit' it now

[Verse 1]
The microphone explodes, shattering the mold
Either drop the hits like de la O or get the fuck off the commode
With the sure shot, sure to make the bodies drop
Drop and don't copy, yo, don't call this a co-op
Terror rains drenchin'
Quenchin' the thirst of the power dons
That five-sided Fistagon
The rotten sore on the face of Mother Earth gets bigger
The trigger’s cold, empty your purse

[Chorus]
Rally 'round the family
With a pocket full of shells
They rally 'round the family
With a pocket full of shells
They rally 'round the family
With a pocket full of shells
They rally 'round the family
With a pocket full of shells

[Verse 2]
Weapons, not food, not homes, not shoes
Not need, just feed the war, cannibal animal, I
Walk the corner to the rubble
That used to be a library, line up to the mind cemetery now
What we don't know keeps the contracts alive and movin'
They don't gotta burn the books, they just remove 'em
While arms warehouses fill as quick as the cells
Rally 'round the family, pockets full of shells
See upcoming rock shows
Get tickets for your favorite artists
You might also like
Killing in the Name
Rage Against the Machine
thanK you aIMee
Taylor Swift
THE HEART PART 6
Drake
[Chorus]
Rally 'round the family
With a pocket full of shells
They rally 'round the family
With a pocket full of shells
They rally 'round the family
With a pocket full of shells
They rally 'round the family
With a pocket full of shells

[Post-Chorus]
Bulls on parade, uh

[Guitar Solo]

[Outro]
Come wit' it now
Come wit' it now
Bulls on parade
Bulls on parade
Bulls on parade
Bulls on parade
Bulls on parade
Bulls on parade"""

_dupe = """The image shows two characters inside a vehicle, likely an airplane or helicopter.

In the foreground is Elena, she has short blonde hair and wears a dark blue blazer over a white shirt with a black tie.

Behind her is Rude, he has a completely bald head and a thin goatee. He wears an all-black suit.

The setting appears to be at night, with stars visible through the window behind them. The interior of the vehicle suggests it may be some type of aircraft or transport vehicle due to its design and controls visible in front of Rude.
"""

class VectorDB():
    def __init__(self, client: openai.AsyncOpenAI, conf):
        self.vector_db: List[Tuple[str, np.ndarray]] = []
        self.client = client
        self.conf = conf
        self._decay_mask = None

    def _make_decay_mask(self, d: int) -> np.ndarray:
        end_weight = getattr(self.conf.rag, "lienar_decay_end", 0.0)
        w = np.linspace(1.0, end_weight, num=d, dtype=np.float32)
        return np.sqrt(w)

    async def _get_embeddings(self, message:str) -> np.ndarray:
        response = await self.client.embeddings.create(
            model=self.conf.rag.embedding_model,
            input=message)
        emb = np.asarray(response.data[0].embedding, dtype=np.float32)
        D = emb.shape[0]

        truncate_d = getattr(self.conf.rag, "truncate_to_k", D)
        if truncate_d < D:
            emb = emb[:truncate_d]

        if getattr(self.conf.rag, "linear_decay", False):
            if self._decay_mask is None:                
                self._decay_mask = self._make_decay_mask(D)
            emb *= self._decay_mask
        
        if getattr(self.conf.rag, "normalize", False):
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb /= norm

        return emb

    async def get_top_n_matches(self, message: str, k: int) -> List[Tuple[str, float]]:
        """ Gets the top k matches from the vector db
        Using numpy to avoid ballooning dist by adding pytorch, cpu should be fine
        """
        target = await self._get_embeddings(message)
        #print(target_embedding) # looks correct, various values between -1 to +1
        print(f"target.shape: {target.shape}") # 1024
        
        if len(self.vector_db) == 0:
            return []
        
        texts = list([x[0] for x in self.vector_db])
        vectors = np.array([x[1] for x in self.vector_db])
        
        vectors_norm = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        target_norm = target / np.linalg.norm(target)
        similarities = np.dot(vectors_norm, target_norm) # (109,)
        print(f"similarities: {similarities}")

        pairs = list(zip(texts, similarities))
        sorted_pairs = sorted(pairs, key=lambda x: -x[1])
        with open("rag_matches.txt", "w") as f:
            f.write(f"QUERY: {message}\n")
            for p in sorted_pairs:
                f.write(f"{p[1]:.3f} {p[0]}\n")
        top_k_matches = sorted_pairs[:k]
        
        return top_k_matches

    async def parse_doc_and_add_embeddings_to_db(self, doc: str):
        paragraphs = [p.strip() for p in doc.split('\n') if p.strip()]
        for p in paragraphs:
            emb = await self._get_embeddings(p)
            print(f"{p}, {emb}")

            self.vector_db.append((p, emb))

        # throwing in a random song lyric as a test that should be low match
        emb = await self._get_embeddings(_lyrics)
        self.vector_db.append((_lyrics, emb))
        
        # test something I know should be 1.00
        emb = await self._get_embeddings(_dupe)
        self.vector_db.append((_dupe, emb))