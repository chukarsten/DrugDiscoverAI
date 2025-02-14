from rdkit import Chem
from rdkit.Chem import Descriptors

analyze_molecule_function = {
    "name": "analyze_molecule",
    "description": "Analyzes a molecule based on its SMILES representation.  Call this if you need to provide information about a molecule.",
    "parameters": {
        "type": "object",
        "properties": {
            "smiles": {
                "type": "string",
                "description": "The SMILES representation of the molecule to analyze."
            }
        },
        "required": ["smiles"],
        "additionalProperties": False
    }
}


def analyze_molecule(smiles):
    if validate_molecule(smiles):
        mol = Chem.MolFromSmiles(smiles)
    if mol:
        molecular_weight = Descriptors.MolWt(mol)
        logP = Descriptors.MolLogP(mol)
        num_atoms = mol.GetNumAtoms()
        num_bonds = mol.GetNumBonds()
        return {
            "molecular_weight": molecular_weight,
            "logP": logP,
            "num_atoms": num_atoms,
            "num_bonds": num_bonds,
        }
    else:
        return None


validate_molecule_function = {
    "name": "validate_molecule",
    "description": "Validates a molecule based on its SMILES representation.  Call this if you need to determine whether a molecule is a valid molecule or not.",
    "parameters": {
        "type": "object",
        "properties": {
            "smiles": {
                "type": "string",
                "description": "The SMILES representation of the molecule to validate."
            }
        },
        "required": ["smiles"],
        "additionalProperties": False
    }
}


def validate_molecule(smiles):
    mol = Chem.MolFromSmiles(smiles)
    return mol is not None


tools = [{"type": "function", "function": validate_molecule_function},
         {"type": "function", "function": analyze_molecule_function}]

if __name__ == "__main__":
    pass
