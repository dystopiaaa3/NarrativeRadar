from core.services.narrative_service import NarrativeService


def main():

    service = NarrativeService()


    print(
        "Testing Narrative Service..."
    )


    print(
        "\nTRENDING:"
    )

    print(
        service.trending(
            "6h"
        )
    )


    print(
        "\nTOP:"
    )

    print(
        service.top_narratives()
    )


    print(
        "\nEMERGING:"
    )

    print(
        service.emerging()
    )


    print(
        "\nPULSE:"
    )

    print(
        service.pulse()
    )


    print(
        "\nRADAR:"
    )

    print(
        service.radar()
    )


if __name__ == "__main__":
    main()