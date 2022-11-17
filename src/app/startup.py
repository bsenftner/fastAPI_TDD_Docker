import json   
from app.api.models import NoteSchema, BlogPostSchema
from app.api import crud

from app.config import log

# ---------------------------------------------------------------------------------------
# Called by app startup event, this ensures site_config exists in the db:
async def initialize_database_data( ) -> None:
    
    log.info('looking for site_config...')
    note = await crud.get_note_by_title('site_config')
    if not note:
        
        log.info('site_config not found, creating...')
        data = { "protect_contact": True }
        
        dataP = json.dumps(data) # dump to string
        
        note = NoteSchema(title="site_config",
                          description = "configuration data for admins",
                          data=dataP
                         )
        id = await crud.post_note( payload=note, owner=1)
        log.info(f"created site_config with id {id}.")
    
    else:
        log.info(f"Loaded site config: {note.data}")
        note.data = json.loads(note.data)
        log.info(f"site config recovered: {note.data}")
        
    # ensure initial blog post exists
    log.info("checking if initial blog post exists...")
    blogpost = await crud.get_blogpost(1)
    if not blogpost:
        log.info("creating first blog post payload...")
        first_blogpost_payload = BlogPostSchema(title="hello", description="<p>world</p>", tags="debug")
        log.info(f"posting {first_blogpost_payload}...")
        id = await crud.post_blogpost(first_blogpost_payload,1)
        log.info(f"created first blog post with id {id}.")
        
    else:
        log.info(f"first blog post title is '{blogpost.title}'")
        



