"""
Version information for TokiKanri application.
This file contains the current version number and related metadata.
"""

# Version information
VERSION = "0.0.1"  # Current version based on CHANGELOG.md
VERSION_DATE = "2025-06-20"  # Release date from CHANGELOG.md
COMPANY_NAME = "nncc"  # Company/publisher name

# Version as tuple for programmatic comparisons
VERSION_TUPLE = tuple(map(int, VERSION.split('.')))

def get_version_string(include_date=False):
    """Return a formatted version string.
    
    Parameters
    ----------
    include_date : bool, optional
        Whether to include the release date, by default False
    
    Returns
    -------
    str
        Formatted version string
    """
    if include_date:
        return f"TokiKanri v{VERSION} ({VERSION_DATE})"
    return f"TokiKanri v{VERSION}" 

def get_company_name():
    """Return the company/publisher name.
    
    Returns
    -------
    str
        Company name
    """
    return COMPANY_NAME 