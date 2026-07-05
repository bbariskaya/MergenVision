# Database ERD

```mermaid
erDiagram
    PERSON {
        uuid person_id PK
        string external_person_id
        string source_system
        string first_name
        string last_name
        string full_name
        string national_id_hash
        string national_id_encrypted
        string national_id_masked
        date birth_date
        string gender
        string department
        string title
        string organization
        jsonb details
        boolean is_active
        boolean is_deleted
        timestamp created_at
        timestamp updated_at
    }

    PERSON_PHOTO {
        uuid photo_id PK
        uuid person_id FK
        string image_key
        string original_filename
        string image_content_type
        int width
        int height
        float quality_score
        int face_count
        boolean is_primary
        timestamp created_at
    }

    FACE_SAMPLE {
        uuid sample_id PK
        uuid person_id FK
        uuid photo_id FK
        uuid qdrant_point_id
        string model_name
        string model_version
        int embedding_dimension
        string crop_image_key
        jsonb bounding_box
        float detection_confidence
        float quality_score
        boolean is_indexed
        timestamp indexed_at
        timestamp created_at
    }

    IDENTIFICATION_REQUEST {
        uuid request_id PK
        string status
        string task_type
        string query_image_key
        jsonb details
        timestamp created_at
        timestamp updated_at
    }

    IDENTIFICATION_QUERY_FACE {
        uuid query_face_id PK
        uuid request_id FK
        jsonb bounding_box
        float detection_confidence
        float quality_score
        jsonb embedding_payload
        int face_index
        timestamp created_at
    }

    IDENTIFICATION_RESULT {
        uuid result_id PK
        uuid request_id FK
        uuid query_face_id FK
        uuid person_id FK "nullable"
        uuid photo_id FK "nullable"
        uuid sample_id FK "nullable"
        float similarity_score
        string decision
        int rank
        jsonb candidate_payload
        timestamp created_at
    }

    AUDIT_LOG {
        uuid audit_id PK
        string entity_type
        uuid entity_id
        string action
        string actor
        jsonb payload
        timestamp created_at
    }

    PERSON ||--o{ PERSON_PHOTO : has
    PERSON ||--o{ FACE_SAMPLE : has
    PERSON_PHOTO ||--o{ FACE_SAMPLE : has
    IDENTIFICATION_REQUEST ||--o{ IDENTIFICATION_QUERY_FACE : has
    IDENTIFICATION_REQUEST ||--o{ IDENTIFICATION_RESULT : has
    IDENTIFICATION_QUERY_FACE ||--o{ IDENTIFICATION_RESULT : has
    PERSON ||--o{ IDENTIFICATION_RESULT : "matched_as"
    PERSON_PHOTO ||--o{ IDENTIFICATION_RESULT : "matched_as"
    FACE_SAMPLE ||--o{ IDENTIFICATION_RESULT : "matched_as"
```

## Notes

- `PERSON`: kişi/business bilgileri.
- `PERSON_PHOTO`: kişiye ait orijinal fotoğraf metadata’sı. Fotoğraf dosyası MinIO’da durur.
- `FACE_SAMPLE`: fotoğraftan çıkarılmış yüz sample metadata’sı. Embedding vektörü Qdrant’ta durur; PostgreSQL sadece `qdrant_point_id` referansını tutar.
- `IDENTIFICATION_REQUEST`: her identify/search işleminin trace kaydı. Her response `requestId` döndürür.
- `IDENTIFICATION_QUERY_FACE`: sorgu fotoğrafında tespit edilen yüzler. Multiple face durumunu izlemek için gerekli.
- `IDENTIFICATION_RESULT`: Qdrant’tan gelen top-k adayların ve final decision’ın kalıcı sonucu.
- `AUDIT_LOG`: person create, photo enrollment, delete/update gibi önemli operasyonların güvenli audit kaydı.

> Bulk import / Oracle import ileride ayrı bir future scope olarak ele alınabilir. Gerekirse `import_job` ve `import_job_item` tabloları sonradan eklenir. MVP’de kullanıcılar manuel kişi oluşturur ve kişiye fotoğraf enroll eder.
