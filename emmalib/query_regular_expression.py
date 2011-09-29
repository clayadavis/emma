#!/usr/bin/python

import re

query_regular_expression = re.compile(r"""
			(?is)
			("(?:[^\\]|\\.)*?")|			# double quoted strings
			('(?:[^\\]|\\.)*?')|			# single quoted strings
			(`(?:[^\\]|\\.)*?`)|			# backtick quoted strings
			(/\*.*?\*/)|					# c-style comments
			(\#.*$)|						# shell-style comments
			(\))|							# closing parenthesis 
			([0-9]+(?:\\.[0-9]*)?)|			# numbers
			([,;])|							# comma or semicolon
			([^ \r\n\t\(\)]*[ \r\n\t]*\()|	# opening parenthesis with leading whitespace
			([^ \r\n\t,;()"'`]+)			# everything else...
		""", re.VERBOSE)
        
