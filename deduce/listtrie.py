""" This module contains all functionality for the ListTrie class"""


class ListTrie:
    """
    This class contains an implementation of a ListTrie, which is not much different
    from a normal Trie, except that it accepts lists. It also has a method for
    finding all prefixes of a certain list.
    """

    def __init__(self):
        """ Initiate ListTrie """
        self.root = _ListTrieNode()


    def add(self, list):
        """ Add a list to the ListTrie """
        self.root.add(list, 0)

    def print_all(self):
        """ Print all lists in the ListTrie """
        self.root.print_all(list())

    def find_all(self):
        """ Find all lists in the ListTrie """
        result = []
        self.root.find_all(list(), result)
        return result

    def find_all_prefixes(self, prefix):
        """ Find all lists in the ListTrie that are a prefix of the prefix argument """
        result = []
        self.root.find_all_prefixes(list(), prefix, 0, result)
        return result

class _ListTrieNode:
    """ List Trie Nodes """

    def __init__(self):
        """ Initiate ListTrieNode with empty dictionary and non terminal state """
        self.nodes = {} # empty dict
        self.is_terminal = False

    def add(self, list, position):
        """ Add a list to the ListTrie by adding the current item
        in the list to this ListTrieNode """

        # Last position of the list, make the node terminal
        if position == len(list):
            self.is_terminal = True

        # Else recurse
        else:

            # Current item in the list
            current_item = list[position]

            # If the item is not yet in the dictionary, create a new empty ListTrieNode
            if current_item not in self.nodes:
                self.nodes[current_item] = _ListTrieNode()

            # Recurse on the ListTrieNode corresponding to the current_item
            self.nodes[current_item].add(list, position + 1)

    def print_all(self, list):
        """ Print all lists in the ListTrie """

        # If the ListTrieNode is terminal, print the list
        if self.is_terminal:
            print (list)

        # Else recurse through the ListTrie
        for key, node in self.nodes.iteritems():
            node.print_all(list+[key])

    def find_all(self, list, result):
        """ Find all lists in the ListTrie"""

        # If the ListTrieNode is terminal, append the list to the list of results
        if self.is_terminal:
            result.append(list)

        # Else recurse through the ListTrie
        for key, node in self.nodes.iteritems():
            node.find_all(list+[key], result)

    def find_all_prefixes(self, list, prefix, prefix_pos, result):
        """ Find all lists in the ListTrie that are a prefix of the prefix argument """

        # If the ListTrieNode is terminal, append the list so far to the results
        if self.is_terminal:
            result.append(list)

        # If we have not satisfied the prefix condition yet, continue
        if prefix_pos < len(prefix):

            # Current item in the list
            current_item = prefix[prefix_pos]

            # If the current item is in this node, continue
            if current_item in self.nodes:

                node = self.nodes[current_item]
                key = current_item

                node.find_all_prefixes(list+[key], prefix, prefix_pos+1, result)
