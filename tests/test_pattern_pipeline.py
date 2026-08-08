from core.intelligence.pattern_pipeline import PatternPipeline


def main():

    print("Testing Pattern Intelligence Pipeline...")


    pipeline = PatternPipeline()


    result = pipeline.analyze(
        85,
        85,
        85,
        85
    )


    print()
    print("Detected:")
    print(result["detected_patterns"])


    print()
    print("Matched:")
    print(result["matched_patterns"])


    print()
    print("Learning:")
    print(result["learning"])



if __name__ == "__main__":
    main()