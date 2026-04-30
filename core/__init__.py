"""core package"""
from .detector import detect_all_installations, VWInstallation
from .symlinks import analyze_paths, find_duplicates_by_realpath
from .sql_analyzer import find_target_files, analyze_file, fix_file
from .structure import scan_folder
from .prefs import get_pref, set_pref
