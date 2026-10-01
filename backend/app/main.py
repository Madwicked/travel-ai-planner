from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from sqlalchemy import text

from app.database import engine, Base
from app.routers.trips import router as trips_router
from app.routers.locations import router as locations_router
from app.routers.hotel_content import router as hotel_content_router
from app.routers.places import router as places_router
from app.routers.transports import router as transports_router
from app.routers.hotels import router as hotels_router
from app.routers.itinerary import router as itinerary_router
from app.routers.transfers import router as transfers_router
from app.routers.routing import router as routing_router


app = FastAPI(
    title="Travel AI Planner API",
    version="1.0.0",
    docs_url=None,
)

Base.metadata.create_all(bind=engine)

app.include_router(
    hotel_content_router
)
app.include_router(trips_router)
app.include_router(locations_router)
app.include_router(places_router)
app.include_router(transports_router)
app.include_router(hotels_router)
app.include_router(itinerary_router)
app.include_router(transfers_router)
app.include_router(routing_router)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )

    html = response.body.decode("utf-8")

    dark_css = """
    <style>
        /* =========================================================
           BASE
           ========================================================= */

        html,
        body {
            background: #181A1F !important;
            color: #9DA3AC !important;
        }

        .swagger-ui {
            background: #181A1F !important;
            color: #9DA3AC !important;
        }


        /* =========================================================
           TOPBAR
           ========================================================= */

        .swagger-ui .topbar {
            background: #14161A !important;
            border-bottom: 1px solid #2B2F36 !important;
        }


        /* =========================================================
           INFO / TITLE
           ========================================================= */

        .swagger-ui .info .title {
            color: #B0B6BF !important;
        }

        .swagger-ui .info p,
        .swagger-ui .info li {
            color: #9DA3AC !important;
        }


        /* =========================================================
           TAGS
           ========================================================= */

        .swagger-ui .opblock-tag {
            color: #9DA3AC !important;
        }

        .swagger-ui .opblock-tag:hover {
            color: #B0B6BF !important;
        }


        /* =========================================================
           ENDPOINT BLOCK
           ========================================================= */

        .swagger-ui .opblock {
            background: #1E2127 !important;
            border-color: #30353C !important;
            box-shadow: none !important;
        }

        .swagger-ui .opblock .opblock-summary {
            border-color: #30353C !important;
        }

        .swagger-ui .opblock-summary-path,
        .swagger-ui .opblock-summary-description {
            color: #9DA3AC !important;
        }

        .swagger-ui .opblock-description-wrapper,
        .swagger-ui .opblock-description {
            color: #8F969F !important;
        }

        .swagger-ui .opblock-body {
            background: #1E2127 !important;
        }


        /* =========================================================
           PARAMETERS / RESPONSES SECTION HEADER
           Это именно полоски с надписями Parameters / Responses
           ========================================================= */

                /* Полоски Parameters / Responses */
        .swagger-ui .opblock-section-header {
            background: #292E36 !important;
            border-color: #363C45 !important;
            box-shadow: none !important;
        }
        
        .swagger-ui .opblock-section-header h4 {
            color: #9299A3 !important;
        }
        
        


        /* =========================================================
           PARAMETERS
           ========================================================= */


        
        /* Фон непосредственно под полосками */
        .swagger-ui .parameters-container,
        .swagger-ui .responses-wrapper,
        .swagger-ui .responses-inner,
        .swagger-ui .response {
            background: #20262E !important;
        }

        .swagger-ui .parameters-col_description,
        .swagger-ui .parameter__name,
        .swagger-ui .parameter__type {
            color: #969DA7 !important;
        }

        .swagger-ui .parameter__name.required span {
            color: #A87878 !important;
        }


        /* =========================================================
           TABLES
           ========================================================= */

        .swagger-ui table thead tr th {
            color: #7F8792 !important;
            border-bottom: 1px solid #30353C !important;
        }

        .swagger-ui table tbody tr td {
            color: #969DA7 !important;
            border-bottom: 1px solid #30353C !important;
        }


        /* =========================================================
           INPUTS / TEXTAREA / SELECT
           ========================================================= */

        .swagger-ui input,
        .swagger-ui textarea,
        .swagger-ui select {
            background: #17191E !important;
            color: #969DA7 !important;
            border: 1px solid #383D45 !important;
        }

        .swagger-ui input::placeholder,
        .swagger-ui textarea::placeholder {
            color: #686F79 !important;
        }


        /* =========================================================
           SCHEME CONTAINER
           ========================================================= */

        .swagger-ui .scheme-container {
            background: #1E2127 !important;
            box-shadow: none !important;
            border-bottom: 1px solid #2D3138 !important;
        }


        /* =========================================================
           RESPONSES
           ========================================================= */

        .swagger-ui .responses-wrapper {
            background: #20262E !important;
        }

        .swagger-ui .responses-inner {
            background: #20262E !important;
        }

        .swagger-ui .response {
            background: #20262E !important;
            border-color: #30353C !important;
        }

        .swagger-ui .response-col_status {
            color: #969DA7 !important;
        }

        .swagger-ui .response-col_description {
            color: #8F969F !important;
        }

        .swagger-ui .response-col_links {
            color: #7F8792 !important;
        }


        /* =========================================================
           RESPONSE HEADERS
           ========================================================= */

        .swagger-ui .headers-wrapper {
            background: #1D2229 !important;
        }

        .swagger-ui .headers-wrapper table {
            background: #1D2229 !important;
        }

        .swagger-ui .headers-wrapper td,
        .swagger-ui .headers-wrapper th {
            color: #858C95 !important;
            border-color: #30353C !important;
        }


        /* =========================================================
           RESPONSE BODY / CODE
           ========================================================= */

        .swagger-ui .highlight-code {
            background: #191B1F !important;
            border: 1px solid #2D3238 !important;
        }

        .swagger-ui .microlight {
            color: #969DA7 !important;
        }


        /* =========================================================
           MODELS / SCHEMAS
           ========================================================= */

        .swagger-ui section.models {
            background: #1E2127 !important;
            border-color: #30353C !important;
        }

        .swagger-ui .model-box {
            background: #1E2127 !important;
            color: #969DA7 !important;
        }

        .swagger-ui .model {
            color: #969DA7 !important;
        }

        .swagger-ui .model-title {
            color: #A6ADB6 !important;
        }

        .swagger-ui .prop-type,
        .swagger-ui .prop-format {
            color: #7F8792 !important;
        }


        /* =========================================================
           BUTTONS
           ========================================================= */

        .swagger-ui .btn {
            color: #969DA7 !important;
            border-color: #383D45 !important;
            background: #202329 !important;
        }

        .swagger-ui .btn:hover {
            background: #292D34 !important;
            border-color: #454B54 !important;
        }


        /* =========================================================
           TRY IT OUT
           ========================================================= */

        .swagger-ui .try-out {
            background: #1B1D22 !important;
        }


        /* =========================================================
           MARKDOWN
           ========================================================= */

        .swagger-ui .markdown p,
        .swagger-ui .markdown li {
            color: #8F969F !important;
        }

        .swagger-ui .markdown code {
            background: #252830 !important;
            color: #969DA7 !important;
        }


        /* =========================================================
           LINKS
           ========================================================= */

        .swagger-ui a {
            color: #7898B8 !important;
        }

        .swagger-ui a:hover {
            color: #8DAAC7 !important;
        }


        /* =========================================================
           REQUIRED / OPTIONAL
           ========================================================= */

        .swagger-ui .required {
            color: #A87878 !important;
        }


        /* =========================================================
           FILTER / SEARCH
           ========================================================= */

        .swagger-ui .filter .operation-filter-input {
            background: #17191E !important;
            color: #969DA7 !important;
            border-color: #383D45 !important;
        }


        /* =========================================================
           AUTHORIZATION
           ========================================================= */

        .swagger-ui .auth-container {
            background: #1E2127 !important;
        }

        .swagger-ui .auth-container input {
            background: #17191E !important;
            color: #969DA7 !important;
        }


        /* =========================================================
           ERROR / WARNING BLOCKS
           ========================================================= */

        .swagger-ui .errors-wrapper {
            background: #261D1D !important;
            color: #B28A8A !important;
        }


        /* =========================================================
           SCROLLBARS
           ========================================================= */

        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }

        ::-webkit-scrollbar-track {
            background: #181A1F;
        }

        ::-webkit-scrollbar-thumb {
            background: #343941;
            border-radius: 5px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #454B54;
        }
    </style>
    """

    html = html.replace("</head>", dark_css + "</head>")

    return HTMLResponse(content=html)


@app.get("/")
def root():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "message": "Travel AI Planner API is running",
        "database": "connected",
    }