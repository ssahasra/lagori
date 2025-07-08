#!/usr/bin/env python3

# Copyright Sameer Sahasrabuddhe
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import graphlib
import json
import subprocess
import sys
from typing import Dict, List, Any, Tuple

RequestFields = 'number,headRefName,baseRefName,url,title,author'

def getPullRequest(pr: str) -> Dict[str, Any]:
    try:
        Dump = subprocess.run(['gh', 'pr', 'view', pr,
                            '--json', RequestFields],
                            capture_output=True)
    except FileNotFoundError:
        exit("gh CLI is not installed or not found in PATH")
    if Dump.returncode:
        print("Unable to fetch specified pull request")
        print("Details:")
        print(Dump.stderr.decode('utf-8'))
        sys.exit(1)
    PR = json.loads(Dump.stdout)
    return PR

def getPullRequestsForAuthor(Author: str) -> Dict[str, Dict[str, Any]]:
    try:
        Dump = subprocess.run(['gh', 'pr', 'list',
                            '--author', Author,
                            '--json', RequestFields],
                            capture_output=True)
    except FileNotFoundError:
        exit("gh CLI is not installed or not found in PATH")
    if Dump.returncode:
        print(f"Unable to fetch pull requests for author {Author}")
        print("Details:")
        print(Dump.stderr.decode('utf-8'))
        sys.exit(1)
    Pulls = { x['headRefName']:x for x in json.loads(Dump.stdout) }
    return Pulls

def printReversedStack(Stack: List[str], Pulls: Dict[str, Dict[str, Any]]):
    for Head in reversed(Stack):
        PR = Pulls[Head]
        print(f"  - {PR['title']} [#{PR['number']}]")
        print(f"    {Head}")
        print(f"    {PR['url']}\n")

def printReversedStackList(Stacks: Dict[str, List[str]], Pulls: Dict[str, Dict[str, Any]]):
    print(type(Stacks.keys()))
    for i, Stack in enumerate(Stacks.values(), 1):
        print(f'Stack {i}:\n')
        printReversedStack(Stack, Pulls)

def getStackForPullRequest(RequestId):
    PR = getPullRequest(RequestId)
    Author = PR['author']['login']
    Pulls = getPullRequestsForAuthor(Author)
    Stack = [PR['headRefName']]
    Base = PR['baseRefName']
    while Base in Pulls:
        Stack.append(Base)
        Base = Pulls[Base]['baseRefName']
    return Stack, Pulls

def printAllStacksForAuthor(Author):
    Pulls = getPullRequestsForAuthor(Author)
    TS = graphlib.TopologicalSorter()
    for PR in Pulls.values():
        Base = PR['baseRefName']
        Head = PR['headRefName']
        if Base in Pulls:
            TS.add(Head, Base)
        else:
            TS.add(Head)
    TS.prepare()

    Stacks = dict()
    while TS.is_active():
        # Set of base PRs on which atleast one PR depends.
        # Final stack list will only contain the top PRs.
        UsedBases = set()
        for Head in TS.get_ready():
            TS.done(Head)
            Base = Pulls[Head]['baseRefName']
            if Base in Stacks:
                Stacks[Head] = Stacks[Base] + [Head]
                UsedBases.add(Base)
            else:
                Stacks[Head] = [Head]
        for Base in UsedBases:
            if Base in Stacks:
                Stacks.pop(Base)

    print(f"Stacks for author {Author}:\n")
    print(Stacks)
    printReversedStackList(Stacks, Pulls)

def main():
    parser = argparse.ArgumentParser(description='Show all stacks of pull requests.')
    parser.add_argument('--author', default="@me",
                        help='Show stacks for specified author')
    parser.add_argument('--pr', help='Show the stack headed by specified PR')
    Args = parser.parse_args()

    if Args.pr:
        Stack, Pulls = getStackForPullRequest(Args.pr)
        printReversedStack(Stack, Pulls)
        return 0

    printAllStacksForAuthor(Args.author)
    return 0

if __name__ == "__main__":
    main()
