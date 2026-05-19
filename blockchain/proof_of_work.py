from blockchain.block import Block
from blockchain.crypto_utils import sign_data

def mine_block(block: Block, difficulty: int = 2) -> Block:
    """Mencari target hash dengan prefix 0 berdasarkan tingkat difficulty (Proof of Work)."""
    target = "0" * difficulty
    while block.hash[:difficulty] != target:
        block.nonce += 1
        block.hash = block.calc_hash()
    block.validator_sig = sign_data(block.hash)  # Sign ulang setelah target ketemu
    return block
