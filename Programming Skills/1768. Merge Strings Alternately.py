class Solution(object):
    def mergeAlternately(self, word1, word2):

        result = [] # for storing the merged characters
        i, j = 0, 0
        len1, len2 = len(word1), len(word2)
# here we merge charcters from word1 and word2 one by one
        while i < len1 and j < len2:
            result.append(word1[i])
            result.append(word2[j])
            i+=1
            j+=1
# if one of the words has more characters than the other, with following code we add up the remaining
        while i < len1:
            result.append(word1[i])
            i+=1
        while j < len2:
            result.append(word2[j])
            j+=1

        return ''.join(result)

sol = Solution()
print(sol.mergeAlternately("abc", "pqr"))  # Output: apbqcr
print(sol.mergeAlternately("ab", "pqrs"))  # Output: apbqrs
print(sol.mergeAlternately("abcd", "pq"))  # Output: apbqcd

# Nurali Bakytbek uulu