"""
Example usage of the PR Review Agent API
"""
import asyncio
import httpx


async def review_pr_example():
    """Example: Review a GitHub PR"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/review/pr",
            json={
                "repo_owner": "octocat",
                "repo_name": "Hello-World",
                "pr_number": 1
            },
            timeout=300.0  # 5 minutes timeout for review
        )
        
        if response.status_code == 200:
            review = response.json()
            print("=" * 60)
            print("PR REVIEW RESULTS")
            print("=" * 60)
            print(f"\nSummary: {review['summary']}")
            print(f"\nTotal Comments: {review['total_comments']}")
            print(f"Files Changed: {review['total_files_changed']}")
            
            print("\n" + "=" * 60)
            print("REVIEW COMMENTS")
            print("=" * 60)
            
            for comment in review['comments']:
                print(f"\n[{comment['severity'].upper()}] {comment['category'].upper()}")
                print(f"File: {comment['file_path']}:{comment['line_number']}")
                print(f"Title: {comment['title']}")
                print(f"Description: {comment['description']}")
                if comment.get('suggestion'):
                    print(f"Suggestion: {comment['suggestion']}")
                print("-" * 60)
        else:
            print(f"Error: {response.status_code}")
            print(response.text)


async def review_diff_example():
    """Example: Review a manual diff"""
    diff_text = """diff --git a/test.py b/test.py
index 1234567..abcdefg 100644
--- a/test.py
+++ b/test.py
@@ -1,5 +1,5 @@
 def calculate_total(items):
-    total = 0
-    for item in items:
-        total += item.price
-    return total
+    return sum(item.price for item in items)
+
+def get_user_data(user_id):
+    query = f"SELECT * FROM users WHERE id = {user_id}"
+    return execute_query(query)
"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/review/diff",
            json={
                "diff_text": diff_text
            },
            timeout=300.0
        )
        
        if response.status_code == 200:
            review = response.json()
            print("=" * 60)
            print("DIFF REVIEW RESULTS")
            print("=" * 60)
            print(f"\nSummary: {review['summary']}")
            print(f"\nTotal Comments: {review['total_comments']}")
            
            for comment in review['comments']:
                print(f"\n[{comment['severity'].upper()}] {comment['title']}")
                print(f"{comment['description']}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)


if __name__ == "__main__":
    print("Make sure the API server is running on http://localhost:8000")
    print("\n1. Reviewing GitHub PR...")
    asyncio.run(review_pr_example())
    
    print("\n\n2. Reviewing manual diff...")
    asyncio.run(review_diff_example())

