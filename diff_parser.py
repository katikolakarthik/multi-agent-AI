"""
Parser for Git diffs to extract code changes
"""
from typing import List, Optional
from models import CodeDiff
import re


class DiffParser:
    """Parser for Git diff format"""
    
    @staticmethod
    def parse_diff(diff_text: str) -> List[CodeDiff]:
        """
        Parse a Git diff string into structured CodeDiff objects
        
        Args:
            diff_text: Raw Git diff text
            
        Returns:
            List of CodeDiff objects
        """
        diffs = []
        current_file = None
        current_diff_lines = []
        current_file_path = None
        added_lines = []
        removed_lines = []
        old_content_lines = []
        new_content_lines = []
        in_hunk = False
        old_line_num = 0
        new_line_num = 0
        
        for line in diff_text.split('\n'):
            # File header
            if line.startswith('diff --git'):
                # Save previous file if exists
                if current_file_path and current_diff_lines:
                    diffs.append(CodeDiff(
                        file_path=current_file_path,
                        old_content='\n'.join(old_content_lines) if old_content_lines else None,
                        new_content='\n'.join(new_content_lines) if new_content_lines else None,
                        added_lines=added_lines,
                        removed_lines=removed_lines,
                        diff_text='\n'.join(current_diff_lines)
                    ))
                
                # Reset for new file
                current_diff_lines = [line]
                added_lines = []
                removed_lines = []
                old_content_lines = []
                new_content_lines = []
                in_hunk = False
                old_line_num = 0
                new_line_num = 0
                continue
            
            # Extract file path
            if line.startswith('---'):
                match = re.search(r'^--- a/(.+)$', line)
                if match:
                    current_file_path = match.group(1)
                current_diff_lines.append(line)
                continue
            
            if line.startswith('+++'):
                current_diff_lines.append(line)
                continue
            
            # Hunk header
            if line.startswith('@@'):
                in_hunk = True
                # Extract line numbers from hunk header: @@ -old_start,old_count +new_start,new_count @@
                match = re.search(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
                if match:
                    old_line_num = int(match.group(1))
                    new_line_num = int(match.group(3))
                current_diff_lines.append(line)
                continue
            
            if not in_hunk:
                current_diff_lines.append(line)
                continue
            
            # Code lines
            if line.startswith('+') and not line.startswith('+++'):
                # Added line
                added_lines.append(new_line_num)
                new_content_lines.append(line[1:])  # Remove '+' prefix
                new_line_num += 1
                current_diff_lines.append(line)
            elif line.startswith('-') and not line.startswith('---'):
                # Removed line
                removed_lines.append(old_line_num)
                old_content_lines.append(line[1:])  # Remove '-' prefix
                old_line_num += 1
                current_diff_lines.append(line)
            elif line.startswith(' '):
                # Context line (unchanged)
                old_line_num += 1
                new_line_num += 1
                current_diff_lines.append(line)
            else:
                current_diff_lines.append(line)
        
        # Save last file
        if current_file_path and current_diff_lines:
            diffs.append(CodeDiff(
                file_path=current_file_path,
                old_content='\n'.join(old_content_lines) if old_content_lines else None,
                new_content='\n'.join(new_content_lines) if new_content_lines else None,
                added_lines=added_lines,
                removed_lines=removed_lines,
                diff_text='\n'.join(current_diff_lines)
            ))
        
        return diffs
    
    @staticmethod
    def get_changed_lines(diff: CodeDiff) -> dict:
        """Extract changed lines with context"""
        return {
            "file_path": diff.file_path,
            "added_lines": diff.added_lines,
            "removed_lines": diff.removed_lines,
            "added_code": diff.new_content,
            "removed_code": diff.old_content
        }

