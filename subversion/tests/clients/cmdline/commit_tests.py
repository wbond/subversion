#!/usr/bin/env python
#
#  commit_tests.py:  testing fancy commit cases.
#
#  Subversion is a tool for revision control. 
#  See http://subversion.tigris.org for more information.
#    
# ====================================================================
# Copyright (c) 2000-2001 CollabNet.  All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.  The terms
# are also available at http://subversion.tigris.org/license-1.html.
# If newer versions of this license are posted there, you may use a
# newer version instead, at your option.
#
######################################################################

# General modules
import shutil, string, sys, re, os

# The `svntest' module
import svntest

# Quick macro for auto-generating sandbox names
def sandbox(x):
  return "commit_tests-" + `test_list.index(x)`

# (abbreviation)
path_index = svntest.actions.path_index
  

######################################################################
# Utilities
#

def get_standard_status_list(wc_dir):
  "Return a status list reflecting local mods made by next routine."

  status_list = svntest.actions.get_virginal_status_list(wc_dir, '1')

  ### todo:  use status-hash below instead.

  # `.'
  status_list[0][3]['status'] = '_M'

  # A/B/lambda, A/D
  status_list[5][3]['status'] = 'M '
  status_list[11][3]['status'] = 'M '

  # A/B/E, A/D/H/chi
  status_list[6][3]['status'] = 'R '
  status_list[6][3]['wc_rev'] = '0'
  status_list[18][3]['status'] = 'R '
  status_list[18][3]['wc_rev'] = '0'

  # A/B/E/alpha, A/B/E/beta, A/C, A/D/gamma
  status_list[7][3]['status'] = 'D '
  status_list[8][3]['status'] = 'D '
  status_list[10][3]['status'] = 'D '
  status_list[12][3]['status'] = 'D '
  status_list[15][3]['status'] = 'D '
  
  # A/D/G/pi, A/D/H/omega
  status_list[14][3]['status'] = '_M'
  status_list[20][3]['status'] = 'MM'

  # New things
  status_list.append([os.path.join(wc_dir, 'Q'), None, {},
                      {'status' : 'A ',
                       'wc_rev' : '0',
                       'repos_rev' : '1'}])
  status_list.append([os.path.join(wc_dir, 'Q', 'floo'), None, {},
                      {'status' : 'A ',
                       'wc_rev' : '0',
                       'repos_rev' : '1'}])
  status_list.append([os.path.join(wc_dir, 'A', 'D', 'H', 'gloo'), None, {},
                      {'status' : 'A ',
                       'wc_rev' : '0',
                       'repos_rev' : '1'}])
  status_list.append([os.path.join(wc_dir, 'A', 'B', 'E', 'bloo'), None, {},
                      {'status' : 'A ',
                       'wc_rev' : '0',
                       'repos_rev' : '1'}])

  return status_list
  

def make_standard_slew_of_changes(wc_dir):
  """Make a specific set of local mods to WC_DIR.  These will be used
  by every commit-test.  Verify the 'svn status' output, return 0 on
  success."""

  # Cache current working directory, move into wc_dir
  was_cwd = os.getcwd()
  os.chdir(wc_dir)

  # Add a directory
  os.mkdir('Q')
  svntest.main.run_svn('add', 'Q')
  
  # Remove two directories
  svntest.main.run_svn('rm', os.path.join('A', 'B', 'E'))
  svntest.main.run_svn('rm', os.path.join('A', 'C'))
  
  # Replace one of the removed directories
  svntest.main.run_svn('add', os.path.join('A', 'B', 'E'))
  
  # Make property mods to two directories
  svntest.main.run_svn('propset', 'foo', 'bar', os.curdir)
  svntest.main.run_svn('propset', 'foo2', 'bar2', os.path.join('A', 'D'))
  
  # Add three files
  svntest.main.file_append(os.path.join('A', 'B', 'E', 'bloo'), "hi")
  svntest.main.file_append(os.path.join('A', 'D', 'H', 'gloo'), "hello")
  svntest.main.file_append(os.path.join('Q', 'floo'), "yo")
  svntest.main.run_svn('add', os.path.join('A', 'B', 'E', 'bloo'))
  svntest.main.run_svn('add', os.path.join('A', 'D', 'H', 'gloo'))
  svntest.main.run_svn('add', os.path.join('Q', 'floo'))
  
  # Remove three files
  svntest.main.run_svn('rm', os.path.join('A', 'D', 'G', 'rho'))
  svntest.main.run_svn('rm', os.path.join('A', 'D', 'H', 'chi'))
  svntest.main.run_svn('rm', os.path.join('A', 'D', 'gamma'))
  
  # Replace one of the removed files
  svntest.main.run_svn('add', os.path.join('A', 'D', 'H', 'chi'))
  
  # Make textual mods to two files
  svntest.main.file_append(os.path.join('A', 'B', 'lambda'), "new ltext")
  svntest.main.file_append(os.path.join('A', 'D', 'H', 'omega'), "new otext")
  
  # Make property mods to three files
  svntest.main.run_svn('propset', 'blue', 'azul',
                       os.path.join('A', 'D', 'H', 'omega'))  
  svntest.main.run_svn('propset', 'green', 'verde',
                       os.path.join('Q', 'floo'))
  svntest.main.run_svn('propset', 'red', 'rojo',
                       os.path.join('A', 'D', 'G', 'pi'))  

  # Restore the CWD.
  os.chdir(was_cwd)
  
  # Build an expected status tree.
  status_list = get_standard_status_list(wc_dir)
  expected_status_tree = svntest.tree.build_generic_tree(status_list)

  # Verify status -- all local mods should be present.
  if svntest.actions.run_and_verify_status(wc_dir, expected_status_tree):
    return 1

  return 0


######################################################################
# Tests
#
#   Each test must return 0 on success or non-zero on failure.


#----------------------------------------------------------------------

def commit_one_file():
  "Commit wc_dir/A/D/H/omega. (anchor=A/D/H, tgt=omega)"

  # Bootstrap:  make independent repo and working copy.
  sbox = sandbox(commit_one_file)
  wc_dir = os.path.join (svntest.main.general_wc_dir, sbox)

  if svntest.actions.make_repo_and_wc(sbox): return 1

  # Make standard slew of changes to working copy.
  if make_standard_slew_of_changes(wc_dir): return 1

  # Create expected output tree.
  omega_path = os.path.join(wc_dir, 'A', 'D', 'H', 'omega') 
  output_list = [ [omega_path, None, {}, {'verb' : 'Changing' }] ]
  expected_output_tree = svntest.tree.build_generic_tree(output_list)

  # Created expected status tree.
  status_list = get_standard_status_list(wc_dir) # pre-commit status
  for item in status_list:
    item[3]['repos_rev'] = '2'     # post-commit status
    if (item[0] == omega_path):
      item[3]['wc_rev'] = '2'
      item[3]['status'] = '__'
  expected_status_tree = svntest.tree.build_generic_tree(status_list)

  # Commit the one file.
  return svntest.actions.run_and_verify_commit (wc_dir,
                                                expected_output_tree,
                                                expected_status_tree,
                                                None,
                                                None, None,
                                                None, None,
                                                omega_path)

#----------------------------------------------------------------------

def commit_inclusive_dir():
  "Commit wc_dir/A/D -- includes D. (anchor=A, tgt=D)"

  pass

#----------------------------------------------------------------------

def commit_noninclusive_dir():
  "Commit repos/wc_dir -- does NOT include wc_dir. (anchor=wc_dir, tgt={})"

  pass

#----------------------------------------------------------------------

def commit_multi_targets():
  "Commit multiple targets. (anchor=common parent, target={tgts})"

  pass
  
#----------------------------------------------------------------------

# Regression test for bug reported by Jon Trowbridge:
# 
#    From: Jon Trowbridge <trow@ximian.com>
#    Subject:  svn segfaults if you commit a file that hasn't been added
#    To: dev@subversion.tigris.org
#    Date: 17 Jul 2001 03:20:55 -0500
#    Message-Id: <995358055.16975.5.camel@morimoto>
#   
#    The problem is that report_single_mod in libsvn_wc/adm_crawler.c is
#    called with its entry parameter as NULL, but the code doesn't
#    check that entry is non-NULL before trying to dereference it.
#
# This bug never had an issue number.
#
def commit_unversioned_thing():
  "committing unversioned object produces error"

  sbox = sandbox(commit_unversioned_thing)
  wc_dir = os.path.join (svntest.main.general_wc_dir, sbox)
  
  if svntest.actions.make_repo_and_wc(sbox):
    return 1

  # Create an unversioned file in the wc.
  svntest.main.file_append(os.path.join(wc_dir, 'blorg'), "nothing to see")

  # Commit a non-existent file and *expect* failure:
  return svntest.actions.run_and_verify_commit (wc_dir,
                                                None,
                                                None,
                                                "unversioned",
                                                None, None,
                                                None, None,
                                                os.path.join(wc_dir,'blorg'))

#----------------------------------------------------------------------

# regression test for bug #391

def nested_dir_replacements():
  "Replace two nested dirs, verify empty contents"

  # Bootstrap:  make independent repo and working copy.
  sbox = sandbox(nested_dir_replacements)
  wc_dir = os.path.join (svntest.main.general_wc_dir, sbox)

  if svntest.actions.make_repo_and_wc(sbox): return 1

  # Delete and re-add A/D (a replacement), and A/D/H (another replace).
  svntest.main.run_svn('rm', os.path.join(wc_dir, 'A', 'D'))
  svntest.main.run_svn('add', os.path.join(wc_dir, 'A', 'D'))
  svntest.main.run_svn('add', os.path.join(wc_dir, 'A', 'D', 'H'))
                       
  # For kicks, add new file A/D/bloo.
  svntest.main.file_append(os.path.join(wc_dir, 'A', 'D', 'bloo'), "hi")
  svntest.main.run_svn('add', os.path.join(wc_dir, 'A', 'D', 'bloo'))
  
  # Verify pre-commit status:
  #    - A/D and A/D/H should both be scheduled as "R" at rev 0
  #    - A/D/bloo scheduled as "A" at rev 0
  #    - ALL other children of A/D scheduled as "D" at rev 1

  sl = svntest.actions.get_virginal_status_list(wc_dir, '1')

  sl[path_index(sl, os.path.join(wc_dir, 'A', 'D'))][3]['status'] = "R "
  sl[path_index(sl, os.path.join(wc_dir, 'A', 'D'))][3]['wc_rev'] = "0"  
  sl[path_index(sl, os.path.join(wc_dir, 'A', 'D', 'H'))][3]['status'] = "R "
  sl[path_index(sl, os.path.join(wc_dir, 'A', 'D', 'H'))][3]['wc_rev'] = "0"  
  sl.append([os.path.join(wc_dir, 'A', 'D', 'bloo'), None, {},
             {'status' : 'A ', 'wc_rev' : '0', 'repos_rev' : '1'}])

  sl[path_index(sl, os.path.join(wc_dir, 'A', 'D', 'G'))][3]['status'] = "D "
  sl[path_index(sl, os.path.join(wc_dir, 'A', 'D', 'G', 'pi'))][3]['status'] = "D "
  sl[path_index(sl, os.path.join(wc_dir, 'A', 'D', 'G', 'rho'))][3]['status'] = "D "
  sl[path_index(sl, os.path.join(wc_dir, 'A', 'D', 'G', 'tau'))][3]['status'] = "D "
  sl[path_index(sl, os.path.join(wc_dir, 'A', 'D', 'H', 'chi'))][3]['status'] = "D "
  sl[path_index(sl, os.path.join(wc_dir, 'A', 'D', 'H', 'omega'))][3]['status'] = "D "
  sl[path_index(sl, os.path.join(wc_dir, 'A', 'D', 'H', 'psi'))][3]['status'] = "D "
  sl[path_index(sl, os.path.join(wc_dir, 'A', 'D', 'gamma'))][3]['status'] = "D "
  expected_status_tree = svntest.tree.build_generic_tree(sl)
  if svntest.actions.run_and_verify_status(wc_dir, expected_status_tree):
    return 1

  # Build expected post-commit trees:

  # Create expected output tree.
  output_list = [ [os.path.join(wc_dir, 'A', 'D'),
                   None, {}, {'verb' : 'Replacing' }], # STACKED value!
                  [os.path.join(wc_dir, 'A', 'D', 'H'),
                   None, {}, {'verb' : 'Adding' }],
                  [os.path.join(wc_dir, 'A', 'D', 'bloo'),
                   None, {}, {'verb' : 'Adding' }] ]
  expected_output_tree = svntest.tree.build_generic_tree(output_list)

  # Created expected status tree.
  sl = svntest.actions.get_virginal_status_list(wc_dir, '2')
  for item in sl:
    item[3]['wc_rev'] = '1'
  
  sl[path_index(sl, os.path.join(wc_dir, 'A', 'D'))][3]['wc_rev'] = "2"  
  sl[path_index(sl, os.path.join(wc_dir, 'A', 'D', 'H'))][3]['wc_rev'] = "2"  
  sl.append([os.path.join(wc_dir, 'A', 'D', 'bloo'), None, {},
             {'status' : '_ ', 'wc_rev' : '2', 'repos_rev' : '2'}])

  sl.pop(path_index(sl, os.path.join(wc_dir, 'A', 'D', 'G')))
  sl.pop(path_index(sl, os.path.join(wc_dir, 'A', 'D', 'G', 'pi')))
  sl.pop(path_index(sl, os.path.join(wc_dir, 'A', 'D', 'G', 'rho')))
  sl.pop(path_index(sl, os.path.join(wc_dir, 'A', 'D', 'G', 'tau')))
  sl.pop(path_index(sl, os.path.join(wc_dir, 'A', 'D', 'H', 'chi')))
  sl.pop(path_index(sl, os.path.join(wc_dir, 'A', 'D', 'H', 'omega')))
  sl.pop(path_index(sl, os.path.join(wc_dir, 'A', 'D', 'H', 'psi')))
  sl.pop(path_index(sl, os.path.join(wc_dir, 'A', 'D', 'gamma')))
    
  expected_status_tree = svntest.tree.build_generic_tree(sl)

  # Commit from the top of the working copy and verify output & status.
  return svntest.actions.run_and_verify_commit (wc_dir,
                                                expected_output_tree,
                                                expected_status_tree,
                                                None,
                                                None, None,
                                                None, None,
                                                wc_dir)

#----------------------------------------------------------------------

# Testing part 1 of the "Greg Hudson" problem -- specifically, that
# our use of the "existence=deleted" flag is working properly in cases
# where the parent directory's revision lags behind a deleted child's
# revision.

def hudson_part_1():
  "hudson prob 1.0:  delete file, commit, update"

  # Bootstrap:  make independent repo and working copy.
  sbox = sandbox(hudson_part_1)
  wc_dir = os.path.join (svntest.main.general_wc_dir, sbox)

  if svntest.actions.make_repo_and_wc(sbox): return 1

  # Remove gamma from the working copy.
  gamma_path = os.path.join(wc_dir, 'A', 'D', 'gamma') 
  svntest.main.run_svn('rm', gamma_path)

  # Create expected commit output.
  output_list = [ [gamma_path, None, {}, {'verb' : 'Deleting' }] ]
  expected_output_tree = svntest.tree.build_generic_tree(output_list)
  
  # After committing, status should show no sign of gamma.
  status_list = svntest.actions.get_virginal_status_list(wc_dir, '2')
  for item in status_list:
    item[3]['wc_rev'] = '1'
  status_list.pop(path_index(status_list, gamma_path))
  expected_status_tree = svntest.tree.build_generic_tree(status_list)
  
  # Commit the deletion of gamma and verify.
  if svntest.actions.run_and_verify_commit (wc_dir,
                                            expected_output_tree,
                                            expected_status_tree,
                                            None, None, None, None, None,
                                            wc_dir):
    return 1

  # Now gamma should be marked as `deleted' under the hood.  When we
  # update, we should see NO output at all, and a perfect, virginal
  # status list at revision 2.  (The `deleted' entry should be removed.)
  
  # Expected output of update:  nothing.
  expected_output_tree = svntest.tree.build_generic_tree([])

  # Expected disk tree:  everything but gamma.
  my_greek_tree = svntest.main.copy_greek_tree()
  my_greek_tree.pop(11)  # removing gamma
  expected_disk_tree = svntest.tree.build_generic_tree(my_greek_tree)
  
  # Expected status after update:  totally clean revision 2, minus gamma.
  status_list = svntest.actions.get_virginal_status_list(wc_dir, '2')
  status_list.pop(path_index(status_list, gamma_path))  
  expected_status_tree = svntest.tree.build_generic_tree(status_list)

  return svntest.actions.run_and_verify_update(wc_dir,
                                               expected_output_tree,
                                               expected_disk_tree,
                                               expected_status_tree)

#----------------------------------------------------------------------

# Testing part 1 of the "Greg Hudson" problem -- variation on previous
# test, removing a directory instead of a file this time.

def hudson_part_1_variation_1():
  "hudson prob 1.1:  delete dir, commit, update"

  # Bootstrap:  make independent repo and working copy.
  sbox = sandbox(hudson_part_1_variation_1)
  wc_dir = os.path.join (svntest.main.general_wc_dir, sbox)

  if svntest.actions.make_repo_and_wc(sbox): return 1

  # Remove H from the working copy.
  H_path = os.path.join(wc_dir, 'A', 'D', 'H') 
  svntest.main.run_svn('rm', H_path)

  # Create expected commit output.
  output_list = [ [H_path, None, {}, {'verb' : 'Deleting' }] ]
  expected_output_tree = svntest.tree.build_generic_tree(output_list)
  
  # After committing, status should show no sign of H or its contents
  status_list = svntest.actions.get_virginal_status_list(wc_dir, '2')
  for item in status_list:
    item[3]['wc_rev'] = '1'
  status_list.pop(path_index(status_list, H_path))
  status_list.pop(path_index(status_list, os.path.join(H_path, 'chi')))
  status_list.pop(path_index(status_list, os.path.join(H_path, 'omega')))
  status_list.pop(path_index(status_list, os.path.join(H_path, 'psi')))
  expected_status_tree = svntest.tree.build_generic_tree(status_list)
  
  # Commit the deletion of H and verify.
  if svntest.actions.run_and_verify_commit (wc_dir,
                                            expected_output_tree,
                                            expected_status_tree,
                                            None, None, None, None, None,
                                            wc_dir):
    return 1

  # Now H should be marked as `deleted' under the hood.  When we
  # update, we should see NO output at all, and a perfect, virginal
  # status list at revision 2.  (The `deleted' entry should be removed.)
  
  # Expected output of update:  nothing.
  expected_output_tree = svntest.tree.build_generic_tree([])

  # Expected disk tree:  everything but H and its contents.
  my_greek_tree = svntest.main.copy_greek_tree()
  my_greek_tree.pop(16)  # removing H
  my_greek_tree.pop(16)  # removing H/chi
  my_greek_tree.pop(16)  # removing H/psi  
  my_greek_tree.pop(16)  # removing H/omega
  expected_disk_tree = svntest.tree.build_generic_tree(my_greek_tree)

  # Expected status after update:  totally clean revision 2, minus H.
  status_list = svntest.actions.get_virginal_status_list(wc_dir, '2')
  status_list.pop(path_index(status_list, H_path))
  status_list.pop(path_index(status_list, os.path.join(H_path, 'chi')))
  status_list.pop(path_index(status_list, os.path.join(H_path, 'omega')))
  status_list.pop(path_index(status_list, os.path.join(H_path, 'psi')))
  expected_status_tree = svntest.tree.build_generic_tree(status_list)

  return svntest.actions.run_and_verify_update(wc_dir,
                                               expected_output_tree,
                                               expected_disk_tree,
                                               expected_status_tree)

#----------------------------------------------------------------------

# Testing part 1 of the "Greg Hudson" problem -- variation 2.  In this
# test, we make sure that a file that is BOTH `deleted' and scheduled
# for addition can be correctly committed & merged.

def hudson_part_1_variation_2():
  "hudson prob 1.2:  delete, commit, re-add, commit"

  # Bootstrap:  make independent repo and working copy.
  sbox = sandbox(hudson_part_1_variation_2)
  wc_dir = os.path.join (svntest.main.general_wc_dir, sbox)

  if svntest.actions.make_repo_and_wc(sbox): return 1

  # Remove gamma from the working copy.
  gamma_path = os.path.join(wc_dir, 'A', 'D', 'gamma') 
  svntest.main.run_svn('rm', gamma_path)

  # Create expected commit output.
  output_list = [ [gamma_path, None, {}, {'verb' : 'Deleting' }] ]
  expected_output_tree = svntest.tree.build_generic_tree(output_list)
  
  # After committing, status should show no sign of gamma.
  status_list = svntest.actions.get_virginal_status_list(wc_dir, '2')
  for item in status_list:
    item[3]['wc_rev'] = '1'
  status_list.pop(path_index(status_list, gamma_path))
  expected_status_tree = svntest.tree.build_generic_tree(status_list)
  
  # Commit the deletion of gamma and verify.
  if svntest.actions.run_and_verify_commit (wc_dir,
                                            expected_output_tree,
                                            expected_status_tree,
                                            None, None, None, None, None,
                                            wc_dir):
    return 1

  # Now gamma should be marked as `deleted' under the hood.
  # Go ahead and re-add gamma, so that is *also* scheduled for addition.
  svntest.main.run_svn('add', gamma_path)

  # For sanity, examine status: it should show a revision 2 tree with
  # gamma scheduled for addition.
  status_list = svntest.actions.get_virginal_status_list(wc_dir, '2')
  for item in status_list:
    item[3]['wc_rev'] = '1'
    if item[0] == gamma_path:
      item[3]['wc_rev'] = '0'
      item[3]['status'] = 'A '
  expected_status_tree = svntest.tree.build_generic_tree(status_list)

  if svntest.actions.run_and_verify_status (wc_dir, expected_status_tree):
    return 1

  # Create expected commit output.
  #   We should see messages that gamma is Deleting and then Adding,
  #   which results in our "stacked" value of `Replacing'.
  output_list = [ [gamma_path, None, {}, {'verb' : 'Replacing' }] ]
  expected_output_tree = svntest.tree.build_generic_tree(output_list)
  
  # After committing, status should show only gamma at revision 2.
  status_list = svntest.actions.get_virginal_status_list(wc_dir, '3')
  for item in status_list:
    if item[0] != gamma_path:
      item[3]['wc_rev'] = '1'
  expected_status_tree = svntest.tree.build_generic_tree(status_list)

  return svntest.actions.run_and_verify_commit (wc_dir,
                                                expected_output_tree,
                                                expected_status_tree,
                                                None, None, None, None, None,
                                                wc_dir)


#----------------------------------------------------------------------

# Testing part 2 of the "Greg Hudson" problem.
#
# In this test, we make sure that we're UNABLE to commit a propchange
# on an out-of-date directory.

def hudson_part_2():
  "hudson prob 2.0:  prop commit on old dir fails."

  # Bootstrap:  make independent repo and working copy.
  sbox = sandbox(hudson_part_2)
  wc_dir = os.path.join (svntest.main.general_wc_dir, sbox)

  if svntest.actions.make_repo_and_wc(sbox): return 1

  # Remove gamma from the working copy.
  gamma_path = os.path.join(wc_dir, 'A', 'D', 'gamma') 
  svntest.main.run_svn('rm', gamma_path)

  # Create expected commit output.
  output_list = [ [gamma_path, None, {}, {'verb' : 'Deleting' }] ]
  expected_output_tree = svntest.tree.build_generic_tree(output_list)
  
  # After committing, status should show no sign of gamma.
  status_list = svntest.actions.get_virginal_status_list(wc_dir, '2')
  for item in status_list:
    item[3]['wc_rev'] = '1'
  status_list.pop(path_index(status_list, gamma_path))
  expected_status_tree = svntest.tree.build_generic_tree(status_list)
  
  # Commit the deletion of gamma and verify.
  if svntest.actions.run_and_verify_commit (wc_dir,
                                            expected_output_tree,
                                            expected_status_tree,
                                            None, None, None, None, None,
                                            wc_dir):
    return 1

  # Now gamma should be marked as `deleted' under the hood, at
  # revision 2.  Meanwhile, A/D is still lagging at revision 1.

  # Make a propchange on A/D
  svntest.main.run_svn('ps', 'foo', 'bar', os.path.join(wc_dir, 'A', 'D'))

  # Commit and *expect* a repository Merge failure:
  return svntest.actions.run_and_verify_commit (wc_dir,
                                                None,
                                                None,
                                                "Merge conflict",
                                                None, None,
                                                None, None,
                                                wc_dir)


########################################################################
# Run the tests


# list all tests here, starting with None:
test_list = [ None,
              commit_one_file,
              commit_unversioned_thing,
              nested_dir_replacements,
              hudson_part_1,
              hudson_part_1_variation_1,
              hudson_part_1_variation_2,
              hudson_part_2
             ]

if __name__ == '__main__':
  
  ## run the main test routine on them:
  err = svntest.main.run_tests(test_list)

  ## remove all scratchwork: the 'pristine' repository, greek tree, etc.
  ## This ensures that an 'import' will happen the next time we run.
  if os.path.exists(svntest.main.temp_dir):
    shutil.rmtree(svntest.main.temp_dir)

  ## return whatever main() returned to the OS.
  sys.exit(err)


### End of file.
# local variables:
# eval: (load-file "../../../svn-dev.el")
# end:
