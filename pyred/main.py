"""
"""
import argparse
from .molcollection import MolCollection

pdbs = []
itps = []

if __name__ == "__main__":
    collection = MolCollection.from_pdbs(pdbs, itps)
    

