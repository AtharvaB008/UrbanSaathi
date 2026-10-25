from modules.complaint_intelligence import (
    calculate_complaint_similarity,
    find_potential_duplicates,
)


sample_complaints = [
    {
        "report_id": 101,
        "ward_id": 15,
        "category": "Roads & public property",
        "title": "Large pothole near market",
        "description": "Large pothole near the central market entrance.",
    },
    {
        "report_id": 102,
        "ward_id": 15,
        "category": "Roads & public property",
        "title": "Large pothole near market",
        "description": "Large pothole near the central market entrance.",
    },
    {
        "report_id": 103,
        "ward_id": 18,
        "category": "Roads & public property",
        "title": "Large pothole near market",
        "description": "Large pothole near the central market entrance.",
    },
    {
        "report_id": 104,
        "ward_id": 15,
        "category": "Waste & sanitation",
        "title": "Garbage collection problem",
        "description": "Garbage has not been collected near the market.",
    },
]


print("Testing complaint similarity...")

score = calculate_complaint_similarity(
    sample_complaints[0],
    sample_complaints[1],
)

print("Similarity between complaints 101 and 102:", score)

assert score == 1.0, "Identical complaints should have a score of 1.0"

assert calculate_complaint_similarity(
    sample_complaints[0],
    sample_complaints[2],
) == 0.0, "Complaints from different wards should not match"

assert calculate_complaint_similarity(
    sample_complaints[0],
    sample_complaints[3],
) == 0.0, "Complaints from different categories should not match"

matches = find_potential_duplicates(
    sample_complaints,
    similarity_threshold=0.65,
)

print("\nPotential duplicate matches:")

for match in matches:
    print(match)

assert len(matches) == 1, "Exactly one duplicate pair should be detected"

assert matches[0]["report_id_1"] == 101
assert matches[0]["report_id_2"] == 102

print("\nTesting locality-aware duplicate detection...")

complaint_a = {
    "report_id": 201,
    "ward_id": 15,
    "category": "Roads & public property",
    "title": "Large pothole",
    "description": "The road has a large pothole.",
    "locality": "Central Market",
}

complaint_b = {
    "report_id": 202,
    "ward_id": 15,
    "category": "Roads & public property",
    "title": "Large pothole",
    "description": "The road has a large pothole.",
    "locality": "Central Market",
}

complaint_c = {
    "report_id": 203,
    "ward_id": 15,
    "category": "Roads & public property",
    "title": "Large pothole",
    "description": "The road has a large pothole.",
    "locality": "Bus Depot",
}

same_locality_score = calculate_complaint_similarity(
    complaint_a, complaint_b
)

different_locality_score = calculate_complaint_similarity(
    complaint_a, complaint_c
)

print("Same locality score:", same_locality_score)
print("Different locality score:", different_locality_score)

assert same_locality_score == 1.0
assert different_locality_score < 0.65

locality_matches = find_potential_duplicates(
    [complaint_a, complaint_b, complaint_c],
    similarity_threshold=0.65,
)

assert len(locality_matches) == 1
assert locality_matches[0]["report_id_1"] == 201
assert locality_matches[0]["report_id_2"] == 202

print("Locality-aware detection tests passed!")

print("\nTesting landmark-aware duplicate detection...")

landmark_complaints = [
    {
        "report_id": 301,
        "ward_id": 15,
        "category": "Roads & public property",
        "title": "Large pothole",
        "description": "The road has a large pothole.",
        "locality": "Central Market",
        "location_details": "Main market entrance",
    },
    {
        "report_id": 302,
        "ward_id": 15,
        "category": "Roads & public property",
        "title": "Large pothole",
        "description": "The road has a large pothole.",
        "locality": "Central Market",
        "location_details": "Main market entrance",
    },
    {
        "report_id": 303,
        "ward_id": 15,
        "category": "Roads & public property",
        "title": "Large pothole",
        "description": "The road has a large pothole.",
        "locality": "Central Market",
        "location_details": "Railway station",
    },
]

same_landmark_score = calculate_complaint_similarity(
    landmark_complaints[0],
    landmark_complaints[1],
)

different_landmark_score = calculate_complaint_similarity(
    landmark_complaints[0],
    landmark_complaints[2],
)

print("Same landmark score:", same_landmark_score)
print("Different landmark score:", different_landmark_score)

assert same_landmark_score == 1.0
assert different_landmark_score < 0.65

landmark_matches = find_potential_duplicates(
    landmark_complaints,
    similarity_threshold=0.65,
)

assert len(landmark_matches) == 1
assert landmark_matches[0]["report_id_1"] == 301
assert landmark_matches[0]["report_id_2"] == 302

print("Landmark-aware detection tests passed!")

print("\nSUCCESS: All duplicate detection tests passed!")