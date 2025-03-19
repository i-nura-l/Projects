class Solution(object):
    def findTheDifference(self, s, t):
        """
        :type s: str
        :type t: str
        :rtype: str
        """
        s = sum(ord(char) for char in s) # sums up all ord of char in word
        t = sum(ord(char) for char in t)
        return chr(t - s) # by subtracting we can find which character is extra

sol = Solution()
print("Example 1:", sol.findTheDifference("abc", "abce"))  # Output: e

# Nurali Bakytbek uulu