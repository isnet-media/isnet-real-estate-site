"""Match the public/admin field-lock semantics when agents merge CMS edits."""
FIELDS = ['title','short_pitch','long_description','category','subcategory','start_date','end_date','start_time','venue','address','purchase_url','youtube_id','image_credit','image_publishable','image_verified','image_url','thumbnail_url','age_min','age_max','organizer','accessibility','contact_phone','content_source_url','ticket_status']

def merge_event(base, payload):
    result = {**base, **payload}
    if payload.get('overlay_version') == 2:
        locked = set(payload.get('locked_fields') or [])
        for field in FIELDS:
            if field not in locked:
                if field in base:
                    result[field] = base[field]
                else:
                    result.pop(field, None)
    if payload.get('description_manual_override') is True:
        text = result.get('long_description') or ''
        result.update(description=text, series_description=text, editorial_description=text)
    if payload.get('image_manual_override') is True and payload.get('image_data_url'):
        result.update(image_url=payload['image_data_url'], thumbnail_url=payload['image_data_url'], thumbnail_ready=True)
    return result
