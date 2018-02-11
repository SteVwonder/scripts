#!/usr/bin/env python3

import argparse

import pandas as pd


def merge_dfs(bitwarden_df, lastpass_df):
    return bitwarden_df

def convert_bitwarden(bitwarden_df):
    '''
    # Lastpass
    Documentation on expected CSV format: https://helpdesk.lastpass.com/importing-from-other-password-managers/

    ## Select notes from lastpass docs
    Lastpass valid columns: url, username, password, extra, name, grouping, type, hostname
    To import Secure Note data, enter the values as follows: “url” = http://sn, “extra” = the contents of the note. Give the note a “name”, and then consider adding “group”. It is important to leave the username and password columns blank.
    ----
    # Bitwarden
    Bitwarden exported columns: folder,favorite,type,name,notes,fields,login_uri,login_username,login_password,login_totp
    '''
    lp_sn_url_format = "http://sn"

    # Other columns aren't used in lastpass
    for col in ['favorite', 'login_totp', 'type']:
        del bitwarden_df[col]

    rename_dict = {
        'login_uri' : 'url',
        'login_username' : 'username',
        'login_password' : 'password',
        'notes' : 'extra',
        'folder' : 'grouping',
    }
    bitwarden_df.rename(columns=rename_dict, inplace=True)

    has_fields_df = bitwarden_df[pd.notna(bitwarden_df['fields'])]
    print("{} entries have a non-empty 'fields' entry".format(len(has_fields_df)))
    assert len(has_fields_df[has_fields_df['url'] == lp_sn_url_format]) == 0 # ensure none of these are lp formatted
    assert len(has_fields_df[pd.notna(has_fields_df['extra'])]) == 0 # ensure none of these have 'extra' entries as well
    bitwarden_df.loc[has_fields_df.index,'extra'] = has_fields_df['fields']
    del bitwarden_df['fields']

    has_extra_df = bitwarden_df[pd.notna(bitwarden_df['extra'])]
    print("{} entries have notes".format(len(has_extra_df)))
    lp_secure_notes_df = has_extra_df[has_extra_df['url'] == lp_sn_url_format]
    print("\t{} entries are lastpass formatted secure notes".format(len(lp_secure_notes_df)))
    assert lp_secure_notes_df[['username', 'password']].isnull().all().all() # make sure all usernames/passwords are empty

    bw_extra_df = has_extra_df[has_extra_df['url'] != lp_sn_url_format]
    bw_secure_notes_df = bw_extra_df[(bw_extra_df['url'].isnull()) |
                                     ((bw_extra_df['password'].isnull()) & (bw_extra_df['username'].isnull()))]
    print("\t{} entries are bitwarden secure notes".format(len(bw_secure_notes_df)))
    assert bw_secure_notes_df[['username', 'password']].isnull().all().all() # make sure all usernames/passwords are empty
    bitwarden_df.loc[bw_secure_notes_df.index,'url'] = lp_sn_url_format

    has_extra_df = bitwarden_df[pd.notna(bitwarden_df['extra'])]
    bw_extra_df = has_extra_df[has_extra_df['url'] != lp_sn_url_format]
    assert pd.notna(bw_extra_df[['password','url']]).all().all()
    print("\t{} entries are logins with notes".format(len(bw_extra_df)))

    no_url_mask = bitwarden_df['url'].isnull()
    bitwarden_df.loc[no_url_mask,'url'] = lp_sn_url_format
    print("{} entries have no url, setting as secure notes".format(no_url_mask.sum()))

def main():
    bitwarden_df = pd.read_csv(args.bitwarden_csv)
    convert_bitwarden(bitwarden_df)
    merge_dfs(bitwarden_df)
    bitwarden_df.to_csv(args.output_csv, index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('bitwarden_csv')
    parser.add_argument('-o', '--output_csv', default="./converted.csv", help="output filename of coverted csv")
    args = parser.parse_args()

    main()
