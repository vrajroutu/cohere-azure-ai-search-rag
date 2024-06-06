import fitz  # PyMuPDF  
from azure.search.documents.indexes import SearchIndexClient  
from azure.search.documents.indexes.models import (  
    AIStudioModelCatalogName,  
    AzureMachineLearningParameters,  
    AzureMachineLearningVectorizer,  
    HnswAlgorithmConfiguration,  
    HnswParameters,  
    SearchField,  
    SearchFieldDataType,  
    SearchIndex,  
    SearchableField,  
    SimpleField,  
    VectorEncodingFormat,  
    VectorSearch,  
    VectorSearchAlgorithmKind,  
    VectorSearchAlgorithmMetric,  
    VectorSearchProfile  
)  
from azure.search.documents import SearchClient  
from azure.search.documents.models import VectorizableTextQuery  
from azure.core.credentials import AzureKeyCredential  
  
def create_or_update_index(client, index_name, vector_field_type, scoring_uri, authentication_key, model_name):  
    fields = [  
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),  
        SearchField(  
            name="text",  
            type=SearchFieldDataType.String,  
            searchable=True,  
        ),  
        SearchField(  
            name="embedding",  
            type=vector_field_type,  
            vector_search_dimensions=1024,  
            vector_search_profile_name="my-vector-config",  
            hidden=False,  
            stored=True,  
            vector_encoding_format=(  
                VectorEncodingFormat.PACKED_BIT  
                if vector_field_type == "Collection(Edm.Byte)"  
                else None  
            ),  
        ),  
    ]  
    vector_search = VectorSearch(  
        profiles=[  
            VectorSearchProfile(  
                name="my-vector-config",  
                algorithm_configuration_name="my-hnsw",  
                vectorizer="my-vectorizer"  
            )  
        ],  
        algorithms=[  
            HnswAlgorithmConfiguration(  
                name="my-hnsw",  
                kind=VectorSearchAlgorithmKind.HNSW,  
                parameters=HnswParameters(  
                    metric=(  
                        VectorSearchAlgorithmMetric.HAMMING  
                        if vector_field_type == "Collection(Edm.Byte)"  
                        else VectorSearchAlgorithmMetric.COSINE  
                    )  
                ),  
            )  
        ],  
        vectorizers=[  
            AzureMachineLearningVectorizer(  
                name="my-vectorizer",  
                aml_parameters=AzureMachineLearningParameters(  
                    scoring_uri=scoring_uri,  
                    authentication_key=authentication_key,  
                    model_name=model_name,  
                ),  
            )  
        ],  
    )  
    index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search)  
    client.create_or_update_index(index=index)  
  
def index_documents(search_client, documents, embeddings):  
    documents_to_index = [  
        {"id": str(idx), "text": doc, "embedding": emb}  
        for idx, (doc, emb) in enumerate(zip(documents, embeddings))  
    ]  
    search_client.upload_documents(documents=documents_to_index)  
  
def extract_text_from_pdf(pdf_path):  
    doc = fitz.open(pdf_path)  
    text = ""  
    for page in doc:  
        text += page.get_text()  
    return text  
