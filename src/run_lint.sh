#!/bin/bash
pylint **/*.py | grep -v 'W0312\|C0301\|C0103\|C0111'
