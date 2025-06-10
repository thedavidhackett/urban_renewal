from typing import Dict, List, TypeAlias, Tuple

import numpy as np
from spacy.language import Language
from spacy.tokens import DocBin


Label : TypeAlias = Tuple[int, int, str]
LabeledExample : TypeAlias = Tuple[str, List[Label]]

def clean_streetname(streetname : str) -> str:
    """
    Cleans the name of a street
    """
    return streetname.replace('.', '').replace('&', 'and')

def construct_street_name(x : Dict[str, str]) -> str:
    """
    Constructs a street name from usaddress tags
    """
    if not x.get('StreetName', False):
        return np.nan
    street_parts = []
    for key in ['StreetNamePreDirectional', 'StreetName', 'StreetNamePostType', 'StreetNamePostDirectional']:
        part = x.get(key, False)
        if not part:
            continue

        street_parts.append(part)

    return ' '.join(street_parts).strip()


def create_address_label(title : str, street : str) -> Label:
    """
    Will create an address label given a title and a street within that title
    """
    start = title.find(street)
    end  = start + len(street)
    return (start, end, 'ADDRESS')


def examples_to_spacy(dataset : List[LabeledExample], outputfile : str, nlp_obj : Language) -> None:
    """
    Takes a list of labeled examples and converts into spacy format
    """
    count = 0
    db = DocBin()
    for text, annotations in dataset:
        doc = nlp_obj(text)
        ents = []
        for start, end, label in annotations:
            span = doc.char_span(start, end, label=label)
            ents.append(span)
        try:
            doc.ents = ents
            db.add(doc)
        except Exception as e:
            count = count + 1
    print(f'Could not convert {count} examples for {outputfile}')
    db.to_disk(outputfile)