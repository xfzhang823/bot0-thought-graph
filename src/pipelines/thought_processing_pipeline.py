"""Utilities for reading, indexing, and printing thought data."""

from pathlib import Path
from typing import Dict, List, Union
import logging

import logging_config

from bot0_thought_graph.thought_generation import IndexedThoughtReader, ThoughtReader
from utils.generic_utils import read_from_json_file

logger = logging.getLogger(__name__)


def unindexed_thought_processing_pipeline(json_file: Union[Path, str]):
    """
    *This pipeline is intended for analysis and QA data!
    """

    thought_reader = ThoughtReader(read_from_json_file(json_file))

    # Fetch the main idea or theme of the thoughts data
    main_idea = thought_reader.get_idea()
    print("\nMain Idea:", main_idea)
    # Example Output: Main Idea: embedded software development

    # Get a list of thought names only
    thought_names = thought_reader.get_thoughts()
    print("\nThought Names:")
    for thought in thought_names:
        print(thought)

    # Retrieve thoughts along with their descriptions
    thoughts_with_descriptions = thought_reader.get_thoughts_and_descriptions()
    print("\nThoughts and Descriptions:")
    for thought in thoughts_with_descriptions:
        print(f"{thought['thought']}: {thought['description']}")
    # Example Output:
    # Definition and Scope: This cluster focuses on basic concepts and definitions...
    # Hardware-Software Integration: This cluster focuses on...

    # Get sub-thoughts for a specific thought
    thought_name = "Definition and Scope"
    sub_thoughts = thought_reader.get_sub_thoughts_for_thought(thought_name)

    # LLM friendly version
    print("\nsub_thoughts - list of dics", sub_thoughts)

    # Human readable version
    print(f"\nSub-Thoughts for '{thought_name}':")
    for sub in sub_thoughts:
        print(f"{sub['name']}: {sub['description']} (Importance: {sub['importance']})")


def indexed_thought_processing_pipeline(
    indexed_model_file: Union[Path, str],
    thought_index: int = 0,
) -> List[Dict[str, Union[str, int, None]]]:
    """
    A pipeline function that reads an unindexed model file, creates an indexed model file,
    and retrieves thought and sub-thought details for a specified thought index.

    Args:
        - indexed_model_file (Union[Path, str]): Path to the indexed model JSON file.
        - thought_index (int, optional): The index of the thought to retrieve sub-thoughts for. Defaults to 0.

    Returns:
        List[Dict[str, Union[str, int, None]]]: A list of dictionaries containing details for each
        sub-thought in the specified thought, with fields for `sub_thought_index`, `name`,
        `description`, `importance`, and `connection_to_next`.

    Workflow:
        - Converts paths to a `Path` object for consistency.
        - Loads and validates the indexed model through the public package reader.
        - Retrieves the main idea, list of thoughts, descriptions, and sub-thoughts for the specified index.
    """
    indexed_model_file = Path(indexed_model_file)

    thought_reader = IndexedThoughtReader(read_from_json_file(indexed_model_file))

    # Get the main idea
    idea = thought_reader.get_idea()

    # Get a list of indexed thoughts
    list_of_thoughts = thought_reader.get_thoughts()

    # Get thoughts with descriptions
    list_of_thoughts_descriptions = thought_reader.get_thoughts_and_descriptions()

    print(f"idea: {idea}")

    # print(f"thoughts: {list_of_thoughts}")

    print(f"thought descriptions: {list_of_thoughts_descriptions}")

    # Get sub-thoughts for a specific thought by index
    sub_thoughts = thought_reader.get_sub_thoughts_for_thought(
        thought_index=thought_index
    )
    logger.info(sub_thoughts)

    return sub_thoughts
