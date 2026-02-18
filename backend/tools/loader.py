import logging

from backend.tools.registry import ToolRegistry


logger = logging.getLogger("robovai.tools.loader")

# Import all tool modules to trigger registration
from backend.tools.fun import (
    RoastTool,
    RizzTool,
    DreamTool,
    HoroscopeTool,
    FightTool,
    JokeTool,
    CatTool,
    DogTool,
    BoredTool,
    TriviaTool,
)
from backend.tools.utility import (
    IpTool,
    CryptoTool,
    ShortenTool,
    PasswordTool,
    UuidTool,
    QrTool,
    WebsiteStatusTool,
    CurrencyTool,
    ColorTool,
    UnitTool,
)
from backend.tools.dev import (
    CodeFixTool,
    SqlTool,
    RegexTool,
    ExplainCodeTool,
    ArduinoTool,
    TimestampTool,
    HashTool,
    LoremTool,
    JsonTool,
    Base64Tool,
)
from backend.tools.life import (
    WeatherTool,
    WikiTool,
    DefinitionTool,
    NumberFactTool,
    HolidayTool,
    TravelPlanTool,
    MealPlanTool,
    WorkoutTool,
    GiftTool,
    MovieRecTool,
)
from backend.tools.edu import (
    SocialTool,
    ScriptTool,
    EmailFormalTool,
    EmailAngryTool,
    Eli5Tool,
    QuizTool,
    BookRecTool,
    TranslateEgyTool,
    GrammarTool,
    SynonymTool,
)
from backend.tools.vision import (
    ScanReceiptTool,
    AnalyzeIdTool,
    ChartInsightsTool,
    AskPdfTool,
    VideoSummaryTool,
    MemeExplainTool,
)
from backend.tools.audio import (
    VoiceNoteTool,
    TtsCustomTool,
    CleanAudioTool,
    MeetingNotesTool,
)
from backend.tools.safety import (
    CheckContentTool,
    LegalSummaryTool,
    OutfitRateTool,
    DishRecipeTool,
    CompareOffersTool,
    TranslateVoiceTool,
)
from backend.tools.image_gen import ImageGenTool
from backend.tools.unsplash import UnsplashSearchTool
from backend.tools.pexels import PexelsSearchTool
from backend.tools.openrouter_image import OpenRouterImageTool
from backend.tools.anidb import AniDBSearchTool
from backend.tools.art_search import ArtSearchTool
from backend.tools.quran import QuranTool
from backend.tools.gofile import GofileTool
from backend.tools.ddownload import DDownloadTool
from backend.tools.imgbb import ImgBBTool
from backend.tools.currency_enhanced import CurrencyEnhancedTool
from backend.tools.email_validator import EmailValidatorTool
from backend.tools.timezone import TimezoneTool
from backend.tools.image_charts import ImageChartsTool
from backend.tools.kroki import KrokiTool
from backend.tools.qr_advanced import QRAdvancedTool
from backend.tools.quickchart import QuickChartTool
from backend.tools.dictionary import DictionaryTool
from backend.tools.wikipedia import WikipediaTool
from backend.tools.calc_advanced import AdvancedCalculatorTool
from backend.tools.chuck_norris import ChuckNorrisTool
from backend.tools.random_fact import RandomFactTool
from backend.tools.random_dog import RandomDogTool
from backend.tools.cat_fact import CatFactTool
from backend.tools.country_info import CountryInfoTool
from backend.tools.http_cat import HTTPCatTool
from backend.tools.trivia import TriviaTool
from backend.tools.joke_api import JokeAPITool
from backend.tools.advice_slip import AdviceSlipTool
from backend.tools.bored_api import BoredAPITool
from backend.tools.ip_geo import IPGeoTool
from backend.tools.uuid_gen import UUIDGeneratorTool
from backend.tools.user_agent import UserAgentTool
from backend.tools.random_user import RandomUserTool
from backend.tools.quote import QuoteTool
from backend.tools.github_user import GitHubUserTool
from backend.tools.color_info import ColorInfoTool
from backend.tools.meme import MemeTool

# 🆕 Custom Python Tools (Pure Logic, No External APIs)
from backend.tools.custom_utils import (
    QuickChartTool as CustomQuickChartTool,
    MathSolverTool,
    TextAnalyzerTool,
    TextCaseTool,
    PasswordStrengthTool,
    DateCalculatorTool,
    RandomPickerTool,
    UnitConverterTool,
    DiagramTool,
)

# 🚀 Advanced Agent Tools (Manus-level capabilities)
from backend.tools.advanced import (
    DeepResearchTool,
    PresentationTool,
    CodeRunnerTool,
    FileCreatorTool,
    WebScraperTool,
    YouTubeTool,
)

# 🆕 Generators & Creators (NEW!)
from backend.tools.generators import (
    LandingPageTool,
    EmailComposerTool,
    DocumentWriterTool,
    CodeGeneratorTool,
    StudyPlanTool,
    CVBuilderTool,
)


def register_all_tools():
    """
    Registers all 100+ tools into the ToolRegistry.
    This function should be called on app startup.
    """
    tools = [
        # Fun
        RoastTool,
        RizzTool,
        DreamTool,
        HoroscopeTool,
        FightTool,
        JokeTool,
        CatTool,
        DogTool,
        BoredTool,
        TriviaTool,
        # Utility
        IpTool,
        CryptoTool,
        ShortenTool,
        PasswordTool,
        UuidTool,
        QrTool,
        WebsiteStatusTool,
        CurrencyTool,
        ColorTool,
        UnitTool,
        # Dev
        CodeFixTool,
        SqlTool,
        RegexTool,
        ExplainCodeTool,
        ArduinoTool,
        TimestampTool,
        HashTool,
        LoremTool,
        JsonTool,
        Base64Tool,
        # Life
        WeatherTool,
        WikiTool,
        DefinitionTool,
        NumberFactTool,
        HolidayTool,
        TravelPlanTool,
        MealPlanTool,
        WorkoutTool,
        GiftTool,
        MovieRecTool,
        # Education
        SocialTool,
        ScriptTool,
        EmailFormalTool,
        EmailAngryTool,
        Eli5Tool,
        QuizTool,
        BookRecTool,
        TranslateEgyTool,
        GrammarTool,
        SynonymTool,
        # Vision & Documents (Phase 7)
        ScanReceiptTool,
        AnalyzeIdTool,
        ChartInsightsTool,
        AskPdfTool,
        VideoSummaryTool,
        MemeExplainTool,
        # Voice & Audio (Phase 8)
        VoiceNoteTool,
        TtsCustomTool,
        CleanAudioTool,
        MeetingNotesTool,
        # Safety & Business (Phase 9)
        CheckContentTool,
        LegalSummaryTool,
        OutfitRateTool,
        DishRecipeTool,
        CompareOffersTool,
        TranslateVoiceTool,
        # Image Generation (NEW - Free!)
        ImageGenTool,
        # Image Search from Unsplash (NEW!)
        UnsplashSearchTool,
        # Image Search from Pexels (NEW!)
        PexelsSearchTool,
        # Advanced AI Image Generation via OpenRouter (NEW!)
        OpenRouterImageTool,
        # Entertainment & Art (NEW!)
        AniDBSearchTool,
        ArtSearchTool,
        # Islamic Content (NEW!)
        QuranTool,
        # Cloud Storage (NEW!)
        GofileTool,
        DDownloadTool,
        ImgBBTool,
        # Enhanced Utilities (NEW!)
        CurrencyEnhancedTool,
        EmailValidatorTool,
        TimezoneTool,
        QRAdvancedTool,
        DictionaryTool,
        WikipediaTool,
        AdvancedCalculatorTool,
        # Entertainment & Fun (NEW!)
        ChuckNorrisTool,
        RandomFactTool,
        RandomDogTool,
        CatFactTool,
        CountryInfoTool,
        HTTPCatTool,
        TriviaTool,
        JokeAPITool,
        AdviceSlipTool,
        BoredAPITool,
        # Utilities & Info (NEW!)
        IPGeoTool,
        UUIDGeneratorTool,
        UserAgentTool,
        RandomUserTool,
        QuoteTool,
        GitHubUserTool,
        ColorInfoTool,
        MemeTool,
        # Data Visualization (NEW!)
        ImageChartsTool,
        KrokiTool,
        QuickChartTool,
        # 🆕 Custom Python Tools (Pure Logic - No APIs!)
        MathSolverTool,  # /math - حل معادلات رياضية
        TextAnalyzerTool,  # /analyze_text - تحليل النصوص
        TextCaseTool,  # /case - تحويل حالة النص
        PasswordStrengthTool,  # /check_password - فحص قوة كلمة المرور
        DateCalculatorTool,  # /date_calc - حسابات التاريخ
        RandomPickerTool,  # /pick - اختيار عشوائي
        UnitConverterTool,  # /convert - تحويل الوحدات
        DiagramTool,  # /diagram - مخططات Mermaid
        # 🚀 Advanced Agent Tools (Manus-level!)
        DeepResearchTool,  # /deep_research - بحث عميق متعدد المصادر
        PresentationTool,  # /presentation - إنشاء عروض تقديمية
        CodeRunnerTool,  # /run_code - تنفيذ كود Python
        FileCreatorTool,  # /create_file - إنشاء ملفات
        WebScraperTool,  # /scrape_url - استخراج محتوى الويب
        YouTubeTool,  # /youtube_transcript - تفريغ فيديو يوتيوب
        # 🆕 Generators & Creators (NEW!)
        LandingPageTool,  # /landing_page - إنشاء صفحات هبوط HTML
        EmailComposerTool,  # /compose_email - كتابة إيميلات احترافية
        DocumentWriterTool,  # /write_document - كتابة مستندات منظمة
        CodeGeneratorTool,  # /generate_code - توليد أكواد برمجية
        StudyPlanTool,  # /study_plan - خطط دراسية مخصصة
        CVBuilderTool,  # /cv_builder - إنشاء سيرة ذاتية
    ]

    count = 0
    for t in tools:
        ToolRegistry.register(t)
        count += 1

    logger.info("Successfully registered %s tools (Manus-Level Agent Ready).", count)
