/*
 * switch.c:  implement 'switch' feature via wc & ra interfaces.
 *
 * ====================================================================
 * Copyright (c) 2000-2002 CollabNet.  All rights reserved.
 *
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.  The terms
 * are also available at http://subversion.tigris.org/license-1.html.
 * If newer versions of this license are posted there, you may use a
 * newer version instead, at your option.
 *
 * This software consists of voluntary contributions made by many
 * individuals.  For exact contribution history, see the revision
 * history and logs, available at http://subversion.tigris.org/.
 * ====================================================================
 */

/* ==================================================================== */



/*** Includes. ***/

#include <assert.h>

#include "svn_wc.h"
#include "svn_client.h"
#include "svn_string.h"
#include "svn_error.h"
#include "svn_path.h"
#include "client.h"



/*** Code. ***/

/* This feature is essentially identical to 'svn update' (see
   ./update.c), but with two differences:

     - the reporter->finish_report() routine needs to make the server
       run delta_dirs() on two *different* paths, rather than on two
       identical paths.

     - after the update runs, we need to more than just
       ensure_uniform_revision;  we need to rewrite all the entries'
       URL attributes.
*/


svn_error_t *
svn_client_switch (const svn_delta_edit_fns_t *before_editor,
                   void *before_edit_baton,
                   const svn_delta_edit_fns_t *after_editor,
                   void *after_edit_baton,
                   svn_client_auth_baton_t *auth_baton,
                   svn_stringbuf_t *path,
                   svn_stringbuf_t *switch_url,
                   svn_revnum_t revision,
                   apr_time_t tm,
                   svn_boolean_t recurse,
                   svn_wc_notify_func_t notify_restore,
                   void *notify_baton,
                   apr_pool_t *pool)
{
  const svn_delta_edit_fns_t *switch_editor;
  void *switch_edit_baton;
  const svn_ra_reporter_t *reporter;
  void *report_baton;
  svn_wc_entry_t *entry;
  svn_stringbuf_t *anchor, *target, *URL;
  svn_error_t *err;
  void *ra_baton, *session;
  svn_ra_plugin_t *ra_lib;

  /* Sanity check.  Without these, the switch is meaningless. */
  assert (path != NULL);
  assert (path->len > 0);
  assert (switch_url != NULL);
  assert (switch_url->len > 0);

  /* If both REVISION and TM are specified, this is an error.
     They mostly likely contradict one another. */
  if ((revision != SVN_INVALID_REVNUM) && tm)
    return
      svn_error_create(SVN_ERR_CL_MUTUALLY_EXCLUSIVE_ARGS, 0, NULL, pool,
                       "Cannot specify _both_ revision and time.");

  /* Use PATH to get the update's anchor and targets. */
  SVN_ERR (svn_wc_get_actual_target (path, &anchor, &target, pool));

  /* Get full URL from the ANCHOR;  this is the URL we will open an RA
     session to. */
  SVN_ERR (svn_wc_entry (&entry, anchor, pool));
  if (! entry)
    return svn_error_createf
      (SVN_ERR_WC_OBSTRUCTED_UPDATE, 0, NULL, pool,
       "svn_client_update: %s is not under revision control", anchor->data);
  if (! entry->url)
    return svn_error_createf
      (SVN_ERR_WC_ENTRY_MISSING_URL, 0, NULL, pool,
       "svn_client_update: entry '%s' has no URL", anchor->data);
  URL = svn_stringbuf_dup (entry->url, pool);

  /* Fetch the switch (update) editor.  If REVISION is invalid, that's
     okay; the RA driver will call editor->set_target_revision() later
     on. */
  SVN_ERR (svn_wc_get_switch_editor (anchor,
                                     target,
                                     revision,
                                     switch_url,
                                     recurse,
                                     &switch_editor,
                                     &switch_edit_baton,
                                     pool));

  /* Wrap it up with outside editors. */
  svn_delta_wrap_editor (&switch_editor, &switch_edit_baton,
                         before_editor, before_edit_baton,
                         switch_editor, switch_edit_baton,
                         after_editor, after_edit_baton, pool);

  /* Get the RA vtable that matches working copy's current URL. */
  SVN_ERR (svn_ra_init_ra_libs (&ra_baton, pool));
  SVN_ERR (svn_ra_get_ra_library (&ra_lib, ra_baton, URL->data, pool));
  
  /* Open an RA session to this URL */
  SVN_ERR (svn_client__open_ra_session (&session, ra_lib, URL, anchor,
                                        TRUE, TRUE, auth_baton, pool));
  
  /* If TM is given, convert the time into a revision number. */
  if (tm)
    SVN_ERR (ra_lib->get_dated_revision (session, &revision, tm));

  /* ### Note: the whole RA interface below will probably change soon. */ 

  /* Tell RA to do a update of URL+TARGET to REVISION; if we pass an
     invalid revnum, that means RA will use the latest revision. */
  SVN_ERR (ra_lib->do_switch (session,
                              &reporter, &report_baton,
                              revision,
                              target,
                              recurse,
                              switch_url,
                              target ? TRUE : FALSE,
                              switch_editor, switch_edit_baton));

  /* Drive the reporter structure, describing the revisions within
     PATH.  When we call reporter->finish_report, the
     update_editor will be driven by svn_repos_dir_delta. */ 
  err = svn_wc_crawl_revisions (path, reporter, report_baton,
                                TRUE, recurse,
                                notify_restore, notify_baton,
                                pool);
  
  /* Sleep for one second to ensure timestamp integrity. */
  apr_sleep (APR_USEC_PER_SEC * 1);

  if (err)
    return err;

  /* Close the RA session. */
  SVN_ERR (ra_lib->close (session));


  return SVN_NO_ERROR;
}



/* 
 * local variables:
 * eval: (load-file "../svn-dev.el")
 * end: */
