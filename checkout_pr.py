#!/usr/bin/env python3

import requests
import os
import subprocess
import argparse
import sys
from configure_build_test import cmake_configure_build_test

def run(*args):
  command = ['git'] + list(args)
  try:
    result = subprocess.run(command, check=True, text=True, capture_output=True)
    return result.stdout
  except subprocess.CalledProcessError as e:
    s = " "
    print(f"Command [{s.join(command)}] exit with code {e.returncode}")
    print(f"Command output: {e.output}")
    print(f"Command stderr: {e.stderr}")
    sys.exit(e.returncode)

def get_current_branch_name():
  return run("rev-parse", "--abbrev-ref", "HEAD").rstrip('\r\n')

def submodule_update_init_recursive():
  return run("submodule", "update", "--init", "--recursive")

# we assume that every submodule tracking "master" branch.
# If that is not true additional workaround needed to determine submodule branch name.
def checkout_all_submodules():
  run("submodule", "foreach", "--recursive", "git", "checkout", "master")

def update_all_submodules():
  checkout_all_submodules()
  submodule_update_init_recursive()

def switch_to_branch(branch_name):
  CURRENT_BRANCH = get_current_branch_name()
  if CURRENT_BRANCH == branch_name:
    print(f"we are already on source branch <{branch_name}>")
  else:
    print(f"switch branch from <{CURRENT_BRANCH}> to <{branch_name}>")
    run("checkout", "--recurse-submodules", branch_name)
    update_all_submodules()

def create_and_checkout_branch(branch_name):
  print(f"create and checkout branch <{branch_name}>")
  run("checkout", "-b", branch_name)

def merge_branch_to_current(branch_name):
  CURRENT_BRANCH = get_current_branch_name()
  print(f"merge <{branch_name}> to <{CURRENT_BRANCH}>")
  run("merge", branch_name)

def checkout_pr(pr_number, from_branch, to_branch, to_sha):
  pr_branch_name = f"pr{pr_number}_{from_branch}_{to_branch}"
  print(f"checkout_pr to branch:<{pr_branch_name}>")
  run("fetch", "origin", f"pull/{pr_number}/head:{pr_branch_name}")
  return pr_branch_name

def clone_repo(clone_url):
  print(f"clone from:<{clone_url}>")
  run("clone", clone_url)

def main():
  parser = argparse.ArgumentParser(description="""
  This script does:
    1. Figure out source and destination branch names.
    2. Create new branch from destination branch.
    3. Merge source branch to destination branch.
  """)
  parser.add_argument("-PR_TITLE", help="Pull request title.")
  parser.add_argument("-FROM_BRANCH", help="Pull request source branch name.")
  parser.add_argument("-FROM_SHA", help="Commit SHA which should be treated as HEAD of source branch.")
  parser.add_argument("-TO_BRANCH", help="Pull request destination branch name.")
  parser.add_argument("-TO_SHA", help="Commit SHA which should be treated as HEAD of destination branch.")
  parser.add_argument("-CLONE_URL", help="URL which can be used in command:$ git clone URL")
  parser.add_argument("-OWNER_NAME", help="Repository owner name.")
  parser.add_argument("-REPO_NAME", help="Repository name.")
  parser.add_argument("-PR_NUMBER", help="Pull request number.")
  parser.add_argument("-CI_WORK_PATH", default=os.getenv('./'), help="CI working directory.")

  args = parser.parse_args()

  PR_TITLE = args.PR_TITLE
  
  # get source and destination branch names
  FROM_BRANCH = args.FROM_BRANCH
  FROM_SHA = args.FROM_SHA
  TO_BRANCH = args.TO_BRANCH
  TO_SHA = args.TO_SHA

  CLONE_URL = args.CLONE_URL
  REPO_NAME = args.REPO_NAME
  OWNER_NAME = args.OWNER_NAME
  PR_NUMBER = args.PR_NUMBER
  CI_WORK_PATH = args.CI_WORK_PATH

  print(f"pull request <{PR_NUMBER}> FROM_BRANCH:<{FROM_BRANCH}> to TO_BRANCH:<{TO_BRANCH}>")
  print(f"FROM_SHA:<{FROM_SHA}> to TO_SHA:<{TO_SHA}>")
  print(f"CLONE_URL:<{CLONE_URL}>")
  print(f"REPO_NAME:<{REPO_NAME}>")
  print(f"OWNER_NAME:<{OWNER_NAME}>")
  print(f"CI_WORK_PATH:<{CI_WORK_PATH}>")

  path = os.path.join(CI_WORK_PATH, OWNER_NAME, REPO_NAME, f"pr{PR_NUMBER}")
  print(f"path:<{path}>")
  os.makedirs(path, exist_ok=True)
  
  os.chdir(path)
  PROJECT_ROOT_PATH = os.path.join(path, REPO_NAME)
  if not os.path.isdir(PROJECT_ROOT_PATH):
    clone_repo(CLONE_URL)

  os.chdir(PROJECT_ROOT_PATH)
  switch_to_branch("master")
  pr_branch_name = checkout_pr(PR_NUMBER, FROM_BRANCH, TO_BRANCH, TO_SHA)
  switch_to_branch(pr_branch_name)

  BUILD_DIR = os.path.join(PROJECT_ROOT_PATH, 'build', 'Xcode')
  NOT_CLEAR_BUILD_DIR = False

  cmake_configure_build_test(False, NOT_CLEAR_BUILD_DIR, 'Debug', 'Xcode', BUILD_DIR, PROJECT_ROOT_PATH)
  cmake_configure_build_test(False, True, 'Release', 'Xcode', BUILD_DIR, PROJECT_ROOT_PATH)

  BUILD_DIR = os.path.join(PROJECT_ROOT_PATH, 'build', 'Ninja', 'Debug')
  cmake_configure_build_test(False, NOT_CLEAR_BUILD_DIR, 'Debug', 'Xcode', BUILD_DIR, PROJECT_ROOT_PATH)

  BUILD_DIR = os.path.join(PROJECT_ROOT_PATH, 'build', 'Ninja', 'Release')
  cmake_configure_build_test(False, NOT_CLEAR_BUILD_DIR, 'Release', 'Xcode', BUILD_DIR, PROJECT_ROOT_PATH)

if __name__ == "__main__":
  main()
