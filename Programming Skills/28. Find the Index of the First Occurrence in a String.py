class Solution(object):
    def strStr(self, haystack, needle):
        """
        :type haystack: str
        :type needle: str
        :rtype: int
        """
        return haystack.find(needle)

sol = Solution()
print(sol.strStr("sadbutsad", "sad"))  # Output: 0
print(sol.strStr("leetcode", "leeto"))  # Output: -1

# Nurali Bakytbek uulu