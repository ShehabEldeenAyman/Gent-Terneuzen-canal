"""Normalize observation values between QUDT units."""

from __future__ import annotations

from rdflib import Graph, Literal, Namespace, URIRef


QUDT = Namespace("http://qudt.org/schema/qudt/")
SOSA = Namespace("http://www.w3.org/ns/sosa/")

# Network-free definitions for the conductivity units used by this project.
# Multipliers and offsets convert a value to QUDT's SI reference unit (S/m).
KNOWN_CONVERSIONS = {
    URIRef("http://qudt.org/vocab/unit/MicroS-PER-CentiM"): (1e-4, 0.0),
    URIRef("http://qudt.org/vocab/unit/MilliS-PER-CentiM"): (1e-1, 0.0),
    URIRef("http://qudt.org/vocab/unit/S-PER-M"): (1.0, 0.0),
}


def convert_qudt_value(
    value: float,
    source_multiplier: float,
    source_offset: float,
    target_multiplier: float,
    target_offset: float,
) -> float:
    """Convert via the common SI reference represented by QUDT metadata."""
    si_value = float(value) * source_multiplier + source_offset
    return (si_value - target_offset) / target_multiplier


def _conversion(unit: URIRef, cache: dict[URIRef, tuple[float, float]]):
    if unit in cache:
        return cache[unit]
    if unit in KNOWN_CONVERSIONS:
        cache[unit] = KNOWN_CONVERSIONS[unit]
        return cache[unit]

    unit_graph = Graph()
    unit_graph.parse(str(unit))
    multiplier = unit_graph.value(unit, QUDT.conversionMultiplier)
    offset = unit_graph.value(unit, QUDT.conversionOffset)
    if multiplier is None:
        raise ValueError(f"QUDT unit {unit} has no conversionMultiplier.")
    cache[unit] = (float(multiplier), float(offset) if offset is not None else 0.0)
    return cache[unit]


def transform_unit(graph_directory, NEW_UNIT):
    """Compatibility entry point using the corrected batch implementation."""
    return transform_unit_optimized(graph_directory, NEW_UNIT)


def transform_unit_optimized(graph_directory, NEW_UNIT):
    """Convert every SOSA observation to NEW_UNIT and serialize once.

    Previous code multiplied only by the source unit's SI multiplier. For
    µS/cm -> mS/cm that produced S/m values and then labelled them as mS/cm,
    making the stored number ten times too small. The corrected formula divides
    by the target unit's multiplier after converting through SI.
    """
    graph = Graph()
    target_unit = URIRef(NEW_UNIT)
    cache: dict[URIRef, tuple[float, float]] = {}

    try:
        graph.parse(graph_directory, format="turtle")
        print(f"Successfully loaded {len(graph)} triples.")
        target_multiplier, target_offset = _conversion(target_unit, cache)
        converted = 0

        for subject in set(graph.subjects(predicate=SOSA.hasSimpleResult)):
            source_unit = graph.value(subject, QUDT.hasUnit)
            if source_unit is None or source_unit == target_unit:
                continue
            source_multiplier, source_offset = _conversion(URIRef(source_unit), cache)
            result = graph.value(subject, SOSA.hasSimpleResult)
            if result is None:
                continue
            new_value = convert_qudt_value(
                float(result),
                source_multiplier,
                source_offset,
                target_multiplier,
                target_offset,
            )
            graph.set((subject, SOSA.hasSimpleResult, Literal(new_value)))
            graph.set((subject, QUDT.hasUnit, target_unit))
            converted += 1

        if converted:
            graph.serialize(destination=graph_directory, format="turtle")
            message = f"Converted {converted} observations to {target_unit}."
        else:
            message = f"No transformations needed; observations already use {target_unit}."
        print(message)
        return message
    except Exception as error:
        raise RuntimeError(f"Could not normalize {graph_directory}: {error}") from error


def main():
    transform_unit_optimized(
        "../data/water_link.ttl",
        URIRef("http://qudt.org/vocab/unit/MilliS-PER-CentiM"),
    )


if __name__ == "__main__":
    main()
