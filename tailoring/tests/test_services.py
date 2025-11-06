from django.test import SimpleTestCase

from tailoring.services import AgentKitTailoringService


class AgentKitTailoringServiceTests(SimpleTestCase):
    """Unit tests for utility helpers that do not hit the OpenAI API."""

    def test_normalize_parameters_defaults(self) -> None:
        params = AgentKitTailoringService.normalize_parameters({})
        self.assertGreaterEqual(params["bullets_per_section"], 1)
        self.assertIsInstance(params["sections"], list)
        self.assertTrue(params["tone"])
        self.assertIn("temperature", params)

    def test_normalize_parameters_custom_values(self) -> None:
        params = AgentKitTailoringService.normalize_parameters(
            {
                "sections": "Results\nLeadership",
                "bullets_per_section": "4",
                "temperature": "0.65",
                "tone": "story-driven and persuasive",
                "include_summary": False,
                "include_cover_letter": True,
            }
        )
        self.assertEqual(params["sections"], ["Results", "Leadership"])
        self.assertEqual(params["bullets_per_section"], 4)
        self.assertAlmostEqual(params["temperature"], 0.65)
        self.assertFalse(params["include_summary"])
        self.assertTrue(params["include_cover_letter"])
