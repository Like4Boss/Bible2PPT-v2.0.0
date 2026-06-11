class AlignmentEngine:
    def __init__(self):
        # We will hold the aligned records in a dictionary keyed by (book_id, chapter, verse)
        self.aligned_data = {}
        
    def align(self, ngayok_stream, niv_stream):
        """
        Aligns the two verse streams.
        Returns a tuple: (aligned_records_list, statistics_dict)
        """
        self.aligned_data.clear()
        
        # 1. Consume ngayok stream
        for v in ngayok_stream:
            key = (v["book_id"], v["chapter"], v["verse"])
            self.aligned_data[key] = {
                "book_id": v["book_id"],
                "chapter": v["chapter"],
                "verse": v["verse"],
                "ngayok": v["text"],
                "niv": None
            }
                
        # 2. Consume niv stream
        for v in niv_stream:
            key = (v["book_id"], v["chapter"], v["verse"])
            if key in self.aligned_data:
                self.aligned_data[key]["niv"] = v["text"]
            else:
                self.aligned_data[key] = {
                    "book_id": v["book_id"],
                    "chapter": v["chapter"],
                    "verse": v["verse"],
                    "ngayok": None,
                    "niv": v["text"]
                }
                
        # Sort keys to maintain standard Bible ordering
        sorted_keys = sorted(self.aligned_data.keys())
        aligned_records = [self.aligned_data[key] for key in sorted_keys]
        
        # Calculate statistics
        stats = self._calculate_stats(aligned_records)
        return aligned_records, stats
        
    def _calculate_stats(self, records: list[dict]) -> dict:
        total_unique_verses = len(records)
        ngayok_count = sum(1 for r in records if r["ngayok"] is not None)
        niv_count = sum(1 for r in records if r["niv"] is not None)
        
        # Details of omitted/missing verses per version
        omitted_details = {
            "ngayok": [],
            "niv": []
        }
        
        for r in records:
            coord = (r["book_id"], r["chapter"], r["verse"])
            if r["ngayok"] is None:
                omitted_details["ngayok"].append(coord)
            if r["niv"] is None:
                omitted_details["niv"].append(coord)
                
        return {
            "total_unique_verses": total_unique_verses,
            "ngayok": {
                "count": ngayok_count,
                "omitted_count": total_unique_verses - ngayok_count,
                "omitted_details": omitted_details["ngayok"]
            },
            "niv": {
                "count": niv_count,
                "omitted_count": total_unique_verses - niv_count,
                "omitted_details": omitted_details["niv"]
            }
        }
