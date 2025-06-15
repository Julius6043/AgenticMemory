#!/usr/bin/env python3
"""
Performance benchmarks for Supabase database components.

This script benchmarks various database operations to help optimize
performance and understand system capabilities.
"""

import os
import sys
import time
import uuid
import statistics
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.database.supabase_client import SupabaseMemoryClient
from src.database.supabase_memory_adapter import SupabaseAgenticMemorySystem


class SupabaseBenchmarks:
    """Performance benchmarks for Supabase database operations."""

    def __init__(self):
        """Initialize the benchmark suite."""
        self.user_id = f"bench_user_{uuid.uuid4().hex[:8]}"
        self.client = None
        self.memory_system = None
        self.created_memory_ids = []
        self.benchmark_results = {}

    def setup(self):
        """Set up the benchmark environment."""
        print("🔧 Setting up benchmark environment...")

        try:
            self.client = SupabaseMemoryClient()

            if not self.client.test_connection():
                print("❌ Cannot connect to Supabase")
                return False

            self.memory_system = SupabaseAgenticMemorySystem(
                user_id=self.user_id,
                model_name="all-MiniLM-L6-v2",
                llm_backend="openai",
                llm_model="gpt-4o-mini",
            )

            print(f"✅ Benchmark environment ready (User: {self.user_id})")
            return True

        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False

    def time_operation(self, operation_name: str, operation_func, *args, **kwargs):
        """Time a database operation."""
        start_time = time.time()
        try:
            result = operation_func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time

            print(f"   ⏱️ {operation_name}: {duration:.3f}s")
            return result, duration, True

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            print(f"   ❌ {operation_name}: Failed in {duration:.3f}s - {e}")
            return None, duration, False

    def benchmark_memory_creation(self, num_memories: int = 50):
        """Benchmark memory creation operations."""
        print(f"\n📝 Benchmarking Memory Creation ({num_memories} memories)...")

        creation_times = []
        successful_creations = 0

        sample_contents = [
            "Artificial intelligence is transforming various industries worldwide.",
            "Machine learning algorithms can identify patterns in large datasets.",
            "Neural networks are inspired by the structure of the human brain.",
            "Deep learning has revolutionized computer vision and natural language processing.",
            "Python is widely used for data science and machine learning applications.",
            "PostgreSQL is a powerful open-source relational database system.",
            "Supabase provides a modern alternative to Firebase with PostgreSQL.",
            "Vector embeddings enable semantic search and similarity matching.",
            "REST APIs provide standardized communication between applications.",
            "Microservices architecture enables scalable and maintainable systems.",
        ]

        for i in range(num_memories):
            content = sample_contents[i % len(sample_contents)]
            content = f"{content} (Benchmark entry {i+1})"

            result, duration, success = self.time_operation(
                f"Create memory {i+1}",
                self.client.create_memory,
                content=content,
                context="Benchmark",
                category="Test",
                keywords=[f"benchmark", f"test{i}"],
                user_id=self.user_id,
            )

            creation_times.append(duration)
            if success and result:
                self.created_memory_ids.append(result)
                successful_creations += 1

        avg_time = statistics.mean(creation_times)
        min_time = min(creation_times)
        max_time = max(creation_times)

        print(f"\n📊 Memory Creation Results:")
        print(f"   Successful: {successful_creations}/{num_memories}")
        print(f"   Average time: {avg_time:.3f}s")
        print(f"   Min time: {min_time:.3f}s")
        print(f"   Max time: {max_time:.3f}s")
        print(f"   Rate: {successful_creations/sum(creation_times):.1f} memories/sec")

        self.benchmark_results["memory_creation"] = {
            "count": num_memories,
            "successful": successful_creations,
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "rate": successful_creations / sum(creation_times),
        }

    def benchmark_memory_retrieval(self, num_retrievals: int = 100):
        """Benchmark memory retrieval operations."""
        print(f"\n🔍 Benchmarking Memory Retrieval ({num_retrievals} retrievals)...")

        if not self.created_memory_ids:
            print("   ⏭️ Skipping (no memories available)")
            return

        retrieval_times = []
        successful_retrievals = 0

        # Test retrieval of random memories
        import random

        for i in range(min(num_retrievals, len(self.created_memory_ids))):
            memory_id = random.choice(self.created_memory_ids)

            result, duration, success = self.time_operation(
                f"Retrieve memory {i+1}", self.client.get_memory, memory_id
            )

            retrieval_times.append(duration)
            if success:
                successful_retrievals += 1

        avg_time = statistics.mean(retrieval_times)
        min_time = min(retrieval_times)
        max_time = max(retrieval_times)

        print(f"\n📊 Memory Retrieval Results:")
        print(f"   Successful: {successful_retrievals}/{len(retrieval_times)}")
        print(f"   Average time: {avg_time:.3f}s")
        print(f"   Min time: {min_time:.3f}s")
        print(f"   Max time: {max_time:.3f}s")
        print(
            f"   Rate: {successful_retrievals/sum(retrieval_times):.1f} retrievals/sec"
        )

        self.benchmark_results["memory_retrieval"] = {
            "count": len(retrieval_times),
            "successful": successful_retrievals,
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "rate": successful_retrievals / sum(retrieval_times),
        }

    def benchmark_search_operations(self, num_searches: int = 20):
        """Benchmark search operations."""
        print(f"\n🔎 Benchmarking Search Operations ({num_searches} searches)...")

        search_queries = [
            "artificial intelligence",
            "machine learning",
            "neural networks",
            "deep learning",
            "python programming",
            "database systems",
            "web development",
            "data science",
            "algorithms",
            "software engineering",
        ]

        # Text search benchmarks
        text_search_times = []
        text_search_results = []

        print("\n   📝 Text Search:")
        for i in range(num_searches):
            query = search_queries[i % len(search_queries)]

            result, duration, success = self.time_operation(
                f"Text search {i+1}",
                self.client.search_memories_by_text,
                query=query,
                limit=10,
                user_id=self.user_id,
            )

            text_search_times.append(duration)
            if success and result:
                text_search_results.append(len(result))

        # Hybrid search benchmarks
        hybrid_search_times = []
        hybrid_search_results = []

        print("\n   🔀 Hybrid Search:")
        for i in range(
            min(num_searches, 10)
        ):  # Fewer hybrid searches as they're more expensive
            query = search_queries[i % len(search_queries)]

            result, duration, success = self.time_operation(
                f"Hybrid search {i+1}",
                self.client.hybrid_search_memories,
                query=query,
                limit=10,
                user_id=self.user_id,
            )

            hybrid_search_times.append(duration)
            if success and result:
                hybrid_search_results.append(len(result))

        # Results
        print(f"\n📊 Search Results:")
        if text_search_times:
            avg_text_time = statistics.mean(text_search_times)
            avg_text_results = (
                statistics.mean(text_search_results) if text_search_results else 0
            )
            print(
                f"   Text Search - Avg time: {avg_text_time:.3f}s, Avg results: {avg_text_results:.1f}"
            )

        if hybrid_search_times:
            avg_hybrid_time = statistics.mean(hybrid_search_times)
            avg_hybrid_results = (
                statistics.mean(hybrid_search_results) if hybrid_search_results else 0
            )
            print(
                f"   Hybrid Search - Avg time: {avg_hybrid_time:.3f}s, Avg results: {avg_hybrid_results:.1f}"
            )

        self.benchmark_results["search"] = {
            "text_search": {
                "avg_time": (
                    statistics.mean(text_search_times) if text_search_times else 0
                ),
                "avg_results": (
                    statistics.mean(text_search_results) if text_search_results else 0
                ),
            },
            "hybrid_search": {
                "avg_time": (
                    statistics.mean(hybrid_search_times) if hybrid_search_times else 0
                ),
                "avg_results": (
                    statistics.mean(hybrid_search_results)
                    if hybrid_search_results
                    else 0
                ),
            },
        }

    def benchmark_batch_operations(self, batch_size: int = 20):
        """Benchmark batch operations."""
        print(f"\n📦 Benchmarking Batch Operations (batch size: {batch_size})...")

        # Prepare batch data
        batch_memories = []
        for i in range(batch_size):
            batch_memories.append(
                {
                    "content": f"Batch memory entry {i+1} containing important information about system performance.",
                    "context": "Batch Test",
                    "category": "Performance",
                    "keywords": [f"batch{i}", "performance", "test"],
                    "tags": ["batch", "benchmark"],
                    "importance_score": 0.5,
                    "user_id": self.user_id,
                }
            )

        # Benchmark bulk creation
        result, duration, success = self.time_operation(
            f"Bulk create {batch_size} memories",
            self.client.bulk_create_memories,
            batch_memories,
        )

        if success and result:
            bulk_rate = len(result) / duration
            print(f"   📊 Bulk creation rate: {bulk_rate:.1f} memories/sec")
            self.created_memory_ids.extend(result)

            self.benchmark_results["batch_operations"] = {
                "batch_size": batch_size,
                "bulk_create_time": duration,
                "bulk_create_rate": bulk_rate,
            }

    def benchmark_memory_system_operations(self, num_operations: int = 30):
        """Benchmark AgenticMemory system operations."""
        print(
            f"\n🧠 Benchmarking Memory System Operations ({num_operations} operations)..."
        )

        # Add notes through memory system
        add_note_times = []
        successful_adds = 0

        for i in range(num_operations):
            content = f"Memory system test note {i+1} about various technical topics and concepts."

            result, duration, success = self.time_operation(
                f"Add note {i+1}",
                self.memory_system.add_note,
                content=content,
                context="System Test",
                category="Technical",
            )

            add_note_times.append(duration)
            if success:
                successful_adds += 1

        # Test related memory retrieval
        related_memory_times = []
        successful_related = 0

        test_queries = [
            "technical concepts",
            "system performance",
            "memory management",
            "data processing",
            "algorithm optimization",
        ]

        for i, query in enumerate(test_queries):
            result, duration, success = self.time_operation(
                f"Get related memories {i+1}",
                self.memory_system.get_related_memories,
                query=query,
                k=5,
            )

            related_memory_times.append(duration)
            if success:
                successful_related += 1

        print(f"\n📊 Memory System Results:")
        if add_note_times:
            avg_add_time = statistics.mean(add_note_times)
            print(
                f"   Add Note - Avg time: {avg_add_time:.3f}s, Success rate: {successful_adds/len(add_note_times)*100:.1f}%"
            )

        if related_memory_times:
            avg_related_time = statistics.mean(related_memory_times)
            print(
                f"   Related Memories - Avg time: {avg_related_time:.3f}s, Success rate: {successful_related/len(related_memory_times)*100:.1f}%"
            )

        self.benchmark_results["memory_system"] = {
            "add_note_avg_time": (
                statistics.mean(add_note_times) if add_note_times else 0
            ),
            "add_note_success_rate": (
                successful_adds / len(add_note_times) if add_note_times else 0
            ),
            "related_memories_avg_time": (
                statistics.mean(related_memory_times) if related_memory_times else 0
            ),
            "related_memories_success_rate": (
                successful_related / len(related_memory_times)
                if related_memory_times
                else 0
            ),
        }

    def benchmark_concurrent_operations(self, num_concurrent: int = 10):
        """Benchmark concurrent operations."""
        print(
            f"\n⚡ Benchmarking Concurrent Operations ({num_concurrent} concurrent)..."
        )

        import threading
        import queue

        results_queue = queue.Queue()

        def concurrent_memory_creation(thread_id):
            """Create memories concurrently."""
            thread_results = []
            for i in range(5):  # Each thread creates 5 memories
                start_time = time.time()
                try:
                    memory_id = self.client.create_memory(
                        content=f"Concurrent memory from thread {thread_id}, item {i+1}",
                        context="Concurrent Test",
                        category="Performance",
                        user_id=self.user_id,
                    )
                    end_time = time.time()
                    thread_results.append(
                        {
                            "thread_id": thread_id,
                            "success": True,
                            "duration": end_time - start_time,
                            "memory_id": memory_id,
                        }
                    )
                except Exception as e:
                    end_time = time.time()
                    thread_results.append(
                        {
                            "thread_id": thread_id,
                            "success": False,
                            "duration": end_time - start_time,
                            "error": str(e),
                        }
                    )

            results_queue.put(thread_results)

        # Start concurrent threads
        threads = []
        start_time = time.time()

        for i in range(num_concurrent):
            thread = threading.Thread(target=concurrent_memory_creation, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = time.time()
        total_duration = end_time - start_time

        # Collect results
        all_results = []
        while not results_queue.empty():
            thread_results = results_queue.get()
            all_results.extend(thread_results)

        successful_operations = sum(1 for r in all_results if r["success"])
        total_operations = len(all_results)
        avg_operation_time = statistics.mean([r["duration"] for r in all_results])

        print(f"\n📊 Concurrent Operations Results:")
        print(f"   Total operations: {total_operations}")
        print(f"   Successful: {successful_operations}")
        print(f"   Success rate: {successful_operations/total_operations*100:.1f}%")
        print(f"   Total time: {total_duration:.3f}s")
        print(f"   Avg operation time: {avg_operation_time:.3f}s")
        print(f"   Throughput: {successful_operations/total_duration:.1f} ops/sec")

        self.benchmark_results["concurrent_operations"] = {
            "num_threads": num_concurrent,
            "total_operations": total_operations,
            "successful_operations": successful_operations,
            "success_rate": successful_operations / total_operations,
            "total_duration": total_duration,
            "avg_operation_time": avg_operation_time,
            "throughput": successful_operations / total_duration,
        }

    def cleanup_benchmark_data(self):
        """Clean up benchmark data."""
        print("\n🧹 Cleaning up benchmark data...")

        try:
            deleted_count = 0
            for memory_id in self.created_memory_ids:
                if self.client.delete_memory(memory_id):
                    deleted_count += 1

            print(
                f"   ✅ Cleaned up {deleted_count}/{len(self.created_memory_ids)} benchmark memories"
            )

        except Exception as e:
            print(f"   ❌ Cleanup failed: {e}")

    def generate_report(self):
        """Generate a comprehensive benchmark report."""
        print("\n" + "=" * 70)
        print("  SUPABASE PERFORMANCE BENCHMARK REPORT")
        print("=" * 70)
        print(f"Benchmark Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"User ID: {self.user_id}")

        for category, results in self.benchmark_results.items():
            print(f"\n📊 {category.upper().replace('_', ' ')}:")
            for key, value in results.items():
                if isinstance(value, float):
                    print(f"   {key}: {value:.3f}")
                else:
                    print(f"   {key}: {value}")

        # Performance summary
        print("\n🎯 PERFORMANCE SUMMARY:")

        if "memory_creation" in self.benchmark_results:
            mc = self.benchmark_results["memory_creation"]
            print(f"   Memory Creation Rate: {mc['rate']:.1f} memories/sec")

        if "memory_retrieval" in self.benchmark_results:
            mr = self.benchmark_results["memory_retrieval"]
            print(f"   Memory Retrieval Rate: {mr['rate']:.1f} retrievals/sec")

        if "search" in self.benchmark_results:
            s = self.benchmark_results["search"]
            print(f"   Text Search Time: {s['text_search']['avg_time']:.3f}s")
            print(f"   Hybrid Search Time: {s['hybrid_search']['avg_time']:.3f}s")

        if "concurrent_operations" in self.benchmark_results:
            co = self.benchmark_results["concurrent_operations"]
            print(f"   Concurrent Throughput: {co['throughput']:.1f} ops/sec")

        print("\n✨ Benchmark completed!")

    def run_all_benchmarks(self):
        """Run all performance benchmarks."""
        print("=" * 70)
        print("  SUPABASE PERFORMANCE BENCHMARKS")
        print("=" * 70)
        print("This will test the performance of various Supabase operations.")

        if not self.setup():
            print("❌ Setup failed. Cannot run benchmarks.")
            return False

        try:
            # Run benchmarks
            self.benchmark_memory_creation(50)
            self.benchmark_memory_retrieval(100)
            self.benchmark_search_operations(20)
            self.benchmark_batch_operations(20)
            self.benchmark_memory_system_operations(30)
            self.benchmark_concurrent_operations(10)

            # Generate report
            self.generate_report()

        except KeyboardInterrupt:
            print("\n\n⏹️ Benchmarks interrupted by user")
        except Exception as e:
            print(f"\n❌ Benchmark failed: {e}")
        finally:
            # Always clean up
            self.cleanup_benchmark_data()

        return True


def main():
    """Main function to run the benchmarks."""
    print("Supabase Performance Benchmarks")
    print("This will test the performance of various database operations.")
    print("\nWarning: This will create and delete test data in your Supabase database.")

    choice = input("\nDo you want to run the benchmarks? (y/n): ").lower().strip()

    if choice in ["y", "yes"]:
        benchmarks = SupabaseBenchmarks()
        benchmarks.run_all_benchmarks()
    else:
        print("Benchmarks cancelled.")


if __name__ == "__main__":
    main()
