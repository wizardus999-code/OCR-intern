from typing import Dict, List
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
import matplotlib.pyplot as plt
from io import BytesIO


class PerformanceAnalytics:
    """Track and analyze OCR processing performance"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize analytics database"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    timestamp TEXT,
                    template_type TEXT,
                    processing_time REAL,
                    confidence_score REAL,
                    cache_hit INTEGER,
                    error_count INTEGER,
                    memory_usage REAL
                )
            """
            )
            conn.commit()

    def record_metrics(self, metrics: Dict):
        """Record performance metrics"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO performance_metrics
                (timestamp, template_type, processing_time, confidence_score,
                 cache_hit, error_count, memory_usage)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    datetime.now().isoformat(),
                    metrics["template_type"],
                    metrics["processing_time"],
                    metrics.get("confidence_score", 0),
                    1 if metrics.get("cache_hit", False) else 0,
                    metrics.get("error_count", 0),
                    metrics.get("memory_usage", 0),
                ),
            )
            conn.commit()

    def get_performance_summary(self, days: int = 7) -> Dict:
        """Get performance summary for recent period"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    AVG(processing_time) as avg_time,
                    AVG(confidence_score) as avg_confidence,
                    SUM(cache_hit) as cache_hits,
                    COUNT(*) as total_docs,
                    SUM(error_count) as total_errors,
                    AVG(memory_usage) as avg_memory
                FROM performance_metrics
                WHERE timestamp > ?
            """,
                (start_date,),
            )

            row = cursor.fetchone()
            if row:
                return {
                    "average_processing_time": row[0],
                    "average_confidence": row[1],
                    "cache_hit_rate": row[2] / row[3] if row[3] > 0 else 0,
                    "total_documents": row[3],
                    "error_rate": row[4] / row[3] if row[3] > 0 else 0,
                    "average_memory_usage": row[5],
                }
            return {}

    def generate_performance_chart(self, metric: str = "processing_time") -> bytes:
        """Generate performance trend chart"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT timestamp, {metric}
                FROM performance_metrics
                ORDER BY timestamp DESC
                LIMIT 100
            """
            )

            data = cursor.fetchall()
            if not data:
                return None

            timestamps, values = zip(*data)
            timestamps = [datetime.fromisoformat(ts) for ts in timestamps]

            plt.figure(figsize=(10, 6))
            plt.plot(timestamps, values)
            plt.title(f'{metric.replace("_", " ").title()} Trend')
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Save plot to bytes
            buf = BytesIO()
            plt.savefig(buf, format="png")
            plt.close()

            return buf.getvalue()

    def get_template_statistics(self) -> List[Dict]:
        """Get processing statistics by template type"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    template_type,
                    COUNT(*) as count,
                    AVG(processing_time) as avg_time,
                    AVG(confidence_score) as avg_confidence,
                    SUM(cache_hit) * 100.0 / COUNT(*) as cache_hit_rate
                FROM performance_metrics
                GROUP BY template_type
            """
            )

            return [
                {
                    "template_type": row[0],
                    "document_count": row[1],
                    "average_processing_time": row[2],
                    "average_confidence": row[3],
                    "cache_hit_rate": row[4],
                }
                for row in cursor.fetchall()
            ]

    def get_error_analysis(self) -> List[Dict]:
        """Get analysis of processing errors"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    template_type,
                    SUM(error_count) as total_errors,
                    COUNT(*) as total_docs,
                    SUM(error_count) * 100.0 / COUNT(*) as error_rate
                FROM performance_metrics
                WHERE error_count > 0
                GROUP BY template_type
                ORDER BY error_rate DESC
            """
            )

            return [
                {
                    "template_type": row[0],
                    "total_errors": row[1],
                    "total_documents": row[2],
                    "error_rate": row[3],
                }
                for row in cursor.fetchall()
            ]
