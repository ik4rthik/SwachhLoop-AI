"""
SwachhLoop AI — Phase 4 AI Services Unit & Integration Tests
============================================================
Tests for modular AI services:
  - WasteDetectorService (detection, classification, corrupted/empty image handling)
  - ComplaintAnalyzerService (NLP, Kalady landmarks, urgency, ambiguity)
  - RouteOptimizerService (geospatial routing, invalid locations, travel estimates)
  - CleanupVerifierService (change score, verification status, missing evidence)
  - KnowledgeRetrieverService (RAG, bilingual English/Malayalam, missing KB)
"""

import io
import pytest
from PIL import Image

from backend.services.waste_detector import (
    RuleBasedWasteDetector,
    VisionWasteDetector,
    get_waste_detector,
    DetectionResult,
)
from backend.services.complaint_analyzer import (
    DeterministicComplaintAnalyzer,
    LLMComplaintAnalyzer,
    UrgencyLevel,
    get_complaint_analyzer,
)
from backend.services.route_optimizer import (
    Location,
    NearestNeighborRouteOptimizer,
    haversine_distance_km,
    get_route_optimizer,
)
from backend.services.cleanup_verifier import (
    ImageDifferenceCleanupVerifier,
    VisionCleanupVerifier,
    VerificationStatus,
    get_cleanup_verifier,
)
from backend.services.knowledge_service import (
    LocalKnowledgeRetriever,
    get_knowledge_service,
)


def create_test_image_bytes(color: tuple = (100, 150, 200), size: tuple = (100, 100)) -> bytes:
    """Helper to generate in-memory image bytes for tests."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ===========================================================================
# 1. Waste Detection Service Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_waste_detector_valid_image():
    detector = RuleBasedWasteDetector()
    img_bytes = create_test_image_bytes()
    result = await detector.detect(img_bytes)

    assert isinstance(result, DetectionResult)
    assert result.detected is True
    assert len(result.waste_types) > 0
    assert result.confidence > 0.0
    assert len(result.bounding_boxes) > 0


@pytest.mark.asyncio
async def test_waste_detector_empty_bytes():
    detector = RuleBasedWasteDetector()
    result = await detector.detect(b"")

    assert result.detected is False
    assert result.waste_types == []
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_waste_detector_corrupted_bytes():
    detector = RuleBasedWasteDetector()
    result = await detector.detect(b"NOT_A_VALID_IMAGE_DATA_BYTES")

    assert result.detected is False
    assert result.waste_types == []
    assert result.confidence == 0.0


@pytest.mark.asyncio
async def test_waste_detector_classification():
    detector = RuleBasedWasteDetector()
    img_bytes = create_test_image_bytes()
    classes = await detector.classify(img_bytes)

    assert isinstance(classes, dict)
    assert "plastic" in classes
    assert all(0.0 <= score <= 1.0 for score in classes.values())


@pytest.mark.asyncio
async def test_vision_waste_detector_fallback():
    # When no API key is provided, VisionWasteDetector delegates to fallback
    detector = VisionWasteDetector(api_key=None)
    img_bytes = create_test_image_bytes()
    result = await detector.detect(img_bytes)

    assert result.detected is True
    assert len(result.waste_types) > 0


# ===========================================================================
# 2. Complaint Analysis Service Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_complaint_analyzer_critical_hazard():
    analyzer = DeterministicComplaintAnalyzer()
    text = "Urgent: hospital syringes and toxic biohazard waste burning near Kalady Junction"
    analysis = await analyzer.analyze(text)

    assert analysis.urgency == UrgencyLevel.CRITICAL
    assert analysis.extracted_location == "Kalady Junction"
    assert "hospital" in str(analysis.waste_types) or "biohazard" in str(analysis.waste_types)
    assert "rapid civic response" in analysis.suggested_action.lower()


@pytest.mark.asyncio
async def test_complaint_analyzer_high_urgency():
    analyzer = DeterministicComplaintAnalyzer()
    text = "Dead animal carcass and overflowing garbage causing bad stench near Mattoor"
    analysis = await analyzer.analyze(text)

    assert analysis.urgency == UrgencyLevel.HIGH
    assert analysis.extracted_location == "Mattoor"


@pytest.mark.asyncio
async def test_complaint_analyzer_routine_complaint():
    analyzer = DeterministicComplaintAnalyzer()
    text = "Some dry leaves and dust swept in front of shop at Temple Road"
    analysis = await analyzer.analyze(text)

    assert analysis.urgency == UrgencyLevel.LOW
    assert analysis.extracted_location == "Temple Road"


@pytest.mark.asyncio
async def test_complaint_analyzer_ambiguous_location():
    analyzer = DeterministicComplaintAnalyzer()
    text = "Waste dumped here"
    analysis = await analyzer.analyze(text)

    assert analysis.extracted_location is None
    assert "ambiguous" in analysis.tags or "incomplete" in analysis.tags


@pytest.mark.asyncio
async def test_complaint_analyzer_empty_text():
    analyzer = DeterministicComplaintAnalyzer()
    analysis = await analyzer.analyze("")

    assert analysis.urgency == UrgencyLevel.LOW
    assert analysis.extracted_location is None
    assert "incomplete" in analysis.tags


@pytest.mark.asyncio
async def test_llm_complaint_analyzer_fallback():
    analyzer = LLMComplaintAnalyzer(api_key=None)
    analysis = await analyzer.analyze("Plastic bottles near Piraroor")

    assert analysis.extracted_location == "Piraroor"
    assert "plastic" in analysis.waste_types


# ===========================================================================
# 3. Route Optimization Service Tests
# ===========================================================================

def test_haversine_distance():
    # Kalady Center (10.1667, 76.4333) to Mattoor (10.1800, 76.4250) is ~1.7 km
    dist = haversine_distance_km(10.1667, 76.4333, 10.1800, 76.4250)
    assert 1.0 < dist < 3.0


@pytest.mark.asyncio
async def test_route_optimizer_multiple_locations():
    optimizer = NearestNeighborRouteOptimizer()
    locations = [
        Location(id="loc1", latitude=10.1667, longitude=76.4333, label="Kalady Junction"),
        Location(id="loc2", latitude=10.1800, longitude=76.4250, label="Mattoor"),
        Location(id="loc3", latitude=10.1550, longitude=76.4400, label="Kanjoor"),
    ]

    result = await optimizer.optimize(locations)

    assert len(result.ordered_locations) == 3
    assert result.estimated_distance_km > 0.0
    assert result.estimated_duration_min > 0.0
    assert result.route_polyline is not None


@pytest.mark.asyncio
async def test_route_optimizer_empty_and_invalid():
    optimizer = NearestNeighborRouteOptimizer()

    # Empty list
    res_empty = await optimizer.optimize([])
    assert res_empty.ordered_locations == []
    assert res_empty.estimated_distance_km == 0.0

    # Invalid coordinates
    invalid_locs = [
        Location(id="bad1", latitude=999.0, longitude=999.0, label="Invalid"),
    ]
    res_invalid = await optimizer.optimize(invalid_locs)
    assert res_invalid.estimated_distance_km == 0.0


@pytest.mark.asyncio
async def test_route_optimizer_travel_time():
    optimizer = NearestNeighborRouteOptimizer()
    origin = Location(id="o", latitude=10.1667, longitude=76.4333)
    destination = Location(id="d", latitude=10.1800, longitude=76.4250)

    time_min = await optimizer.estimate_travel_time(origin, destination)
    assert time_min > 0.0


# ===========================================================================
# 4. Cleanup Verification Service Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_cleanup_verifier_identical_images():
    verifier = ImageDifferenceCleanupVerifier()
    img_bytes = create_test_image_bytes(color=(120, 120, 120))

    result = await verifier.verify(img_bytes, img_bytes)
    assert result.status == VerificationStatus.FAILED
    assert result.change_score < 0.05


@pytest.mark.asyncio
async def test_cleanup_verifier_different_images():
    verifier = ImageDifferenceCleanupVerifier()
    # Before image: dark / cluttered (representing garbage)
    before_img = create_test_image_bytes(color=(20, 30, 20))
    # After image: bright / clear ground
    after_img = create_test_image_bytes(color=(220, 230, 220))

    result = await verifier.verify(before_img, after_img)
    assert result.status == VerificationStatus.VERIFIED_CLEAN
    assert result.change_score >= 0.60
    assert result.confidence > 0.80


@pytest.mark.asyncio
async def test_cleanup_verifier_missing_images():
    verifier = ImageDifferenceCleanupVerifier()
    result = await verifier.verify(b"", b"")

    assert result.status == VerificationStatus.UNVERIFIED
    assert result.confidence == 0.0
    assert result.change_score == 0.0


@pytest.mark.asyncio
async def test_vision_cleanup_verifier_fallback():
    verifier = VisionCleanupVerifier(api_key=None)
    before_img = create_test_image_bytes(color=(20, 20, 20))
    after_img = create_test_image_bytes(color=(200, 200, 200))

    result = await verifier.verify(before_img, after_img)
    assert result.status in [VerificationStatus.VERIFIED_CLEAN, VerificationStatus.PARTIALLY_CLEAN]


# ===========================================================================
# 5. Knowledge / RAG Service Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_knowledge_retriever_english():
    retriever = LocalKnowledgeRetriever(knowledge_path="data/knowledge_base.json")
    articles = await retriever.retrieve("What is the fee for Haritha Karma Sena?")

    assert len(articles) > 0
    assert any("Haritha Karma Sena" in a.title_en for a in articles)


@pytest.mark.asyncio
async def test_knowledge_retriever_malayalam():
    retriever = LocalKnowledgeRetriever(knowledge_path="data/knowledge_base.json")
    query_ml = "ഹരിത കർമ്മ സേന യൂസർ ഫീസ് എത്രയാണ്?"
    resp = await retriever.answer_query(query_ml)

    assert resp.found_knowledge is True
    assert resp.language == "ml"
    assert "50" in resp.answer or "ഫീസ്" in resp.answer


@pytest.mark.asyncio
async def test_knowledge_retriever_unconfigured_file():
    retriever = LocalKnowledgeRetriever(knowledge_path="data/nonexistent_kb.json")
    resp = await retriever.answer_query("How to segregate waste?")

    assert resp.found_knowledge is False
    assert "not configured" in resp.answer.lower()
