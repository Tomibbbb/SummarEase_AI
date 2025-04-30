import sys
import os
import pytest
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.models.summary import Summary


def test_summary_create():
    summary = Summary(
        user_id=1,
        original_text="Original text to be summarized.",
        model_used="bart-large-cnn",
        status="pending"  
    )
    
    assert summary.user_id == 1
    assert summary.original_text == "Original text to be summarized."
    assert summary.model_used == "bart-large-cnn"
    assert summary.status == "pending"
    assert summary.summary_text is None
    


def test_summary_with_result():
    summary = Summary(
        user_id=1,
        original_text="Original text to be summarized.",
        model_used="bart-large-cnn",
        summary_text="This is the summarized text.",
        status="completed"
    )
    
    assert summary.status == "completed"
    assert summary.summary_text == "This is the summarized text."


def test_summary_representation():
    summary = Summary(
        id=1,
        user_id=1,
        original_text="Original text to be summarized.",
        model_used="bart-large-cnn"
    )
    
    
    assert str(summary) is not None
    
    summary.status = "completed"
    
    assert str(summary) is not None