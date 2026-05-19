from database.models import BlockModel
from database.connection import SessionLocal
from blockchain.block import Block
from blockchain.proof_of_work import mine_block

class Blockchain:
    def __init__(self):
        self.difficulty = 2
        self.db = SessionLocal()
        if not self.get_latest():
            self._create_genesis()

    def _create_genesis(self):
        genesis = Block(0, {"info": "AbsenChain Genesis Block"}, "0"*64)
        genesis = mine_block(genesis, self.difficulty)
        self.save_block(genesis)

    def get_latest(self) -> BlockModel:
        return self.db.query(BlockModel).order_by(BlockModel.block_index.desc()).first()

    def add_block(self, data: dict) -> Block:
        latest = self.get_latest()
        new_blk = Block(latest.block_index + 1, data, latest.hash)
        new_blk = mine_block(new_blk, self.difficulty)
        self.save_block(new_blk)
        return new_blk

    def save_block(self, blk: Block):
        bm = BlockModel(
            block_index=blk.index, timestamp=blk.timestamp, data=blk.data,
            previous_hash=blk.previous_hash, nonce=blk.nonce, hash=blk.hash,
            merkle_root=blk.merkle_root, validator_sig=blk.validator_sig
        )
        self.db.add(bm)
        self.db.commit()

    def verify_chain(self) -> tuple[bool, list[str]]:
        """
        Memverifikasi integritas seluruh rantai blockchain (True Domino Effect).
        Returns:
            Tuple (is_valid, list_of_errors)
        """
        blocks = self.db.query(BlockModel).order_by(BlockModel.block_index.asc()).all()
        errors = []
        
        # Simpan hash asli hasil kalkulasi untuk menguji blok berikutnya
        recalculated_hashes = []
        
        for i in range(len(blocks)):
            # Tentukan previous_hash murni yang sejati (turun-temurun dari blok sebelumnya)
            true_previous_hash = recalculated_hashes[i-1] if i > 0 else blocks[i].previous_hash
            
            # 1. Hitung ulang hash murni dari isi data blok saat ini
            current_recalculated_hash = Block.calculate_hash(
                index=blocks[i].block_index,
                timestamp=blocks[i].timestamp,
                data=blocks[i].data,
                previous_hash=true_previous_hash,
                nonce=blocks[i].nonce
            )
            recalculated_hashes.append(current_recalculated_hash)
            
            # 2. Cek apakah data blok ini sendiri telah dimanipulasi
            if blocks[i].hash != current_recalculated_hash:
                # Bedakan pesan error antara manipulasi sumber (awal) vs efek domino
                if i > 0 and blocks[i].previous_hash != recalculated_hashes[i-1]:
                    errors.append(
                        f"Efek Domino (Rantai Putus): Blok #{blocks[i].block_index} terputus karena Blok #{blocks[i-1].block_index} sebelumnya telah dimanipulasi/rusak!"
                    )
                else:
                    errors.append(
                        f"Manipulasi Sumber: Isi data Blok #{blocks[i].block_index} telah diubah secara ilegal!"
                    )
                
        return len(errors) == 0, errors

