import os

root_dir = os.path.abspath(__file__)
print('root_dir=', root_dir)
root_dir = root_dir[:root_dir.rindex("/")] + "/../../"
temp_path = root_dir + '/resources/tmp'

Results_DIR_Name = "dfs_results"

