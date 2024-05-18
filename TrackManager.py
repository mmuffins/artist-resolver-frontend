# TODO: check if aliases can be used for better naming predictions
# TODO: Infer album artist from file path
# TODO: make gui nicer looking
# TODO: colors -> grey out rows where included is disabled
# TODO: colors -> have specific color for values loaded from the db
# TODO: colors -> highlight colors that are different from the current id tag / were edited
# TODO: make gui display error if rest calls fail
# TODO: Add buttons for common tasks, e.g. copy title to original title

import hashlib
import os
import re
import json
import httpx
import asyncio
from typing import List, Optional
from mutagen import id3

class Alias:
  def __init__(self, name: str, type: str, locale: Optional[str], begin: Optional[str], end: Optional[str], type_id: str, ended: bool, sort_name: str, primary: bool):
    self.name = name
    self.type = type
    self.locale = locale
    self.begin = begin
    self.end = end
    self.type_id = type_id
    self.ended = ended
    self.sort_name = sort_name
    self.primary = primary

  def __str__(self):
    return	f"{self.type} ({self.locale}):{self.name}"
  
  def __repr__(self):
    return	f"{self.type} ({self.locale}):{self.name}"

  @classmethod
  def from_dict(cls, data: dict):
    return cls(
      name=data.get("name"),
      type=data.get("type"),
      locale=data.get("locale"),
      begin=data.get("begin"),
      end=data.get("end"),
      type_id=data.get("type-id"),
      ended=data.get("ended"),
      sort_name=data.get("sort-name"),
      primary=data.get("primary", False)
    )

class MbArtistDetails:
  def __init__(self, name: str, type: str, disambiguation: str, sort_name: str, aliases: List[Alias], type_id: str, joinphrase: Optional[str], include:bool = True, id: int = None,):
    self.include: bool = include
    self.name = name
    self.type = type
    self.disambiguation = disambiguation
    self.sort_name = sort_name
    self.mbid = id
    self.aliases = aliases
    self.type_id = type_id
    self.joinphrase = joinphrase
    self.custom_name = sort_name
    self.custom_original_name = name
    self.id: int = id

  def __str__(self):
    return	f"{self.name}"
  
  def __repr__(self):
    return	f"{self.name}"
  
  def get_formatted_artist(self) -> str:
    """
    Returns a formatted string representing the instance.
    """
    display_name = self.custom_name if self.custom_name else self.name
    if self.type.lower() in ["character", "group"]:
      return f"({display_name})"
    return display_name
  
  def update_from_customization(self, data: dict) -> None:
    """
    Update instance details with information from db
    """
    self.include = data['include']
    self.custom_name = data['name']
    self.custom_original_name = data['originalName']
    self.id = data['id']

  @classmethod
  def from_dict(cls, data: dict, artist_list: list['MbArtistDetails']):
    """
    Creates artist objects based on the provided dictionary object
    """
    
    aliases = [Alias.from_dict(alias) for alias in data.get("aliases", [])]
    
    artist = cls(
      name=data.get("name"),
      type=data.get("type"),
      disambiguation=data.get("disambiguation"),
      sort_name=data.get("sort_name"),
      id=data.get("id"),
      aliases=aliases,
      type_id=data.get("type_id"),
      joinphrase=data.get("joinphrase", "")
    )

    if not any(a.mbid == artist.mbid for a in artist_list):
      artist_list.append(artist)

    # Flatten nested artists
    for relation in data.get("relations", []):
      cls.from_dict(relation, artist_list)

  @staticmethod
  def parse_json(json_str: str) -> list['MbArtistDetails']:
    """
    Deserializes an artist_json string into multiple artist objects
    """
    
    data = json.loads(json_str)
    artist_list: list[MbArtistDetails] = []
    for item in data:
      MbArtistDetails.from_dict(item, artist_list)

    return artist_list
  
class SimpleArtistDetails(MbArtistDetails):
  def __init__(self, name: str, type: str, disambiguation: str, sort_name: str, aliases: List[Alias], type_id: str, joinphrase: Optional[str], include: bool = True, product: str = "", product_id: int = None, id: int = -1):
    super().__init__(name, type, disambiguation, sort_name, aliases, type_id, joinphrase, include, id)
    
    self.product = product
    self.product_id = product_id
    self.mbid = self.generate_instance_hash(f"{self.name}-{self.product_id}")

  def __str__(self):
    return f"{self.name}"

  def __repr__(self):
    return f"{self.name}"

  def generate_instance_hash(self, unique_string: str):
    """
    Generates hash that uniquely identifies an instance
    """

    return hashlib.sha256(unique_string.encode()).hexdigest()

  @staticmethod
  def parse_simple_artist(artist_list: list[str], product: str, product_id: int) -> list['SimpleArtistDetails']:
    """
    Deserializes a string containing a list of artists into artist objects 
    """

    split_artists = SimpleArtistDetails.split_artist(artist_list)
    simple_artist_list: List['SimpleArtistDetails'] = []
    for artist in split_artists:
      simple_artist_list.append(SimpleArtistDetails.from_simple_artist(artist, product, product_id))
    return simple_artist_list

  @classmethod
  def from_simple_artist(cls, artist, product: str, product_id: int):
    """
    Creates artist object
    """

    simple_artist = cls(
      include = artist["include"],
      name = artist["name"],
      type = artist["type"],
      disambiguation=None,
      sort_name=None,
      aliases=[],
      id=None,
      type_id=None,
      joinphrase=None,
      product = product,
      product_id = product_id,
    )

    simple_artist.custom_name = artist["name"]
    simple_artist.custom_original_name = None

    return simple_artist
  
  def update_from_simple_artist_dict(self, data: dict) -> None:
    """
    Update instance details with information from db
    """

    self.custom_name = data['artist']
    self.custom_original_name = data['name']
    self.id = data['artistId']

  @staticmethod
  def split_artist_list(artist_list: list[str]) -> list[str]:
    """
    Splits artist string by common delimiters like and, with or feat
    """

    regex = re.compile(r'\s?[,&;、×]\s?|\sand\s|\s?with\s?|\s?feat\.?(?:uring)?\s?')
    result = []

    for artist in artist_list:
      result.extend(regex.split(artist))

    return result

  @staticmethod
  def split_artist_cv(artist):
    """
    Splits artist string containing character and voice artist, e.g. Artist 1(CV: Artist 2)
    """

    regex = re.compile(r'(\s?[\(|（](?:[Cc][Vv][\:|\.|：]?\s?).*[\)|）])')
    split_artists = regex.split(artist)

    # Clean up the results to remove empty strings and potential leading/trailing whitespace
    split_artists = [artist.strip() for artist in split_artists if artist.strip()]

    # Artists with CV information are usually sorted `Character (CV Voice Actor)`
    # For better sorting we want to flip that array to get `(CV Voice Actor); Character`
    split_artists.reverse()
    return split_artists

  @staticmethod
  def extract_cv_artist(cv_artist: str) -> str:
    """
    Extracts the artist name from strings in format (CV: artist)
    """

    regex = re.compile(r'\((?:[Cc][Vv][\:|\.|：]?\s?)([^)]+)\)')
    match = regex.search(cv_artist)
    return match.group(1) if match else None

  @staticmethod
  def split_artist(artist: list[str]):
    """
    Splits artist string into individual artists
    """
    artist_list = SimpleArtistDetails.split_artist_list(artist)
    split_list = []

    for regex_artist in artist_list:
      parts = SimpleArtistDetails.split_artist_cv(regex_artist)
      split_list.extend(SimpleArtistDetails.process_split_artist_parts(parts))

    return split_list

  @staticmethod
  def process_split_artist_parts(parts: list[str]) -> list[str]:
    """
    Process parts of the artist string, splitting by CV and character types.
    """
    for i in range(len(parts)):
      parts[i] = {"type": "Person", "include": True, "name": parts[i]}

    if len(parts) > 1:
      for part in parts:
        # If artist is in brackets and starts with cv, e.g. (cv artist 1) it's a real person
        if part["name"].strip().lower().startswith("(cv"):
          part["name"] = SimpleArtistDetails.extract_cv_artist(part["name"])
          continue
        
        # In all other cases it's either a character or group
        part["type"] = "Character"
        part["include"] = False
    else:
        if parts[i]["name"].strip().lower().startswith("(cv"):
          parts[i]["name"] = SimpleArtistDetails.extract_cv_artist(parts[i]["name"])
        else:
          brackets_match = re.match(r'^\((.*)\)$', parts[i]["name"])
          if brackets_match:
            parts[i]["name"] = brackets_match.group(1)
            parts[i]["type"] = "Character"
            parts[i]["include"] = False

    return parts


  @staticmethod
  def parse_simple_artist_franchise(track_product, track_album_artist, product_list: dict) -> dict:
    """
    Determines correct product for an artist based on a product list
    """
    
    product = {"id": None, "name": None}

    if track_product:
      product["name"] = track_product
    elif track_album_artist:
      product["name"] = track_album_artist
    else:
      # the default product indicating that the track doesn't belong to a franchise is _
      product["name"] = "_"
    
    resolved_product = [p for p in product_list if p["name"] == product["name"].replace(" ", "")]

    if resolved_product:
      return resolved_product[0]
      
    default_product = [p for p in product_list if p["name"] == "_"]
    
    return default_product[0]

class TrackDetails:
  tag_mappings = {
    'TIT2': {"property": "title", "frame": id3.TIT2},
    'TPE1': {"property": "artist", "frame": id3.TPE1},
    'TALB': {"property": "album", "frame": id3.TALB},
    'TPE2': {"property": "album_artist", "frame": id3.TPE2},
    'TIT1': {"property": "grouping", "frame": id3.TIT1},
    'TOAL': {"property": "original_album", "frame": id3.TOAL},
    'TOPE': {"property": "original_artist", "frame": id3.TOPE},
    'TPE3': {"property": "original_title", "frame": id3.TPE3}
  }

  def __init__(self, file_path: str, manager):
    self.file_path: str = file_path
    self.manager: TrackManager = manager
    self.title: str = None
    self.artist: List[str] = None
    self.album: str = None
    self.album_artist: str = None
    self.grouping: str = None
    self.original_album: str = None
    self.original_artist: List[str] = None
    self.original_title: str = None
    self.product: str = None
    self.artist_relations = None
    self.update_file: bool = True
    self.mbArtistDetails: List[MbArtistDetails] = []
    
  def __str__(self):
    return	f"{self.title}"
  
  def __repr__(self):
    return	f"{self.title}"
    
  def get_artist_string(self) -> str:
    """
    Returns a formatted string for all artists of the object
    """

    return "; ".join(self.get_included_artist_list())
  
  def get_included_artist_list(self) -> str:
    """
    Returns a formatted string for all artists of the object
    """

    return [artist.get_formatted_artist() for artist in self.mbArtistDetails if artist.include == True]

  @staticmethod
  def get_id3_value(id3: id3.ID3, tag: str):
    """
    Returns the correct value for an id3 tag
    """

    # some tags commonly contain multiple values and need to be handled accordingly
    value = id3.get(tag)
    if not value:
      return None
    
    match tag:
      case "TPE1":
        return value.text
      case "TOPE":
        return value.text
      case _:
        if(len(value.text) > 1):
          raise ValueError(f"Tag {tag} contains unexpected array value {value.text}")
        return (value.text)[0]

  async def read_file_metadata(self) -> None:
    """
    Reads mp3 tags from a file
    """

    self.id3 = await self.get_id3_object(self.file_path)
    for tag, mapping  in self.tag_mappings.items():
      # some metadata needs to be handled differently

      value = TrackDetails.get_id3_value(self.id3, tag)
      setattr(self, mapping["property"], value)

    # the artist_relations array is not a specific ID3 tag but is stored as text in the general purpose TXXX frame
    artist_relations_frame = next((frame for frame in self.id3.getall("TXXX") if frame.desc == 'artist_relations_json'), None)
    if artist_relations_frame:
      self.artist_relations = artist_relations_frame.text[0]

    await self.create_artist_objects()
  
  async def create_artist_objects (self) -> None:
    """
    Creates artist objects from id3 tags of a file
    """

    if self.artist_relations:
      self.mbArtistDetails = self.manager.parse_mbartist_json(self.artist_relations)
    else:
      self.mbArtistDetails = await self.manager.create_artist_details_from_simple_artist_track(self)

  async def get_id3_object(self, file_path: str):
    """
    Creates object for a file used to read from a file. Moved to separate function to make testing easier
    """

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: id3.ID3(file_path))

  def apply_custom_tag_values(self) -> None:
    """
    Applies customized values to the main tags
    """

    # Some manually edited artists could contain multiple entries
    # e.g. groups, or character-person combnations.
    # Make sure to split on semicolon again to properly write these entries as
    # separate id3 tags
    artists = self.get_included_artist_list() or self.artist
    split_artists = []
    for entry in artists:
      split_artists.extend([artist.strip() for artist in entry.split(';')])
    self.artist = split_artists

  def save_file_metadata(self) -> None:
    """
    Writes changed id3 tags back to the filesystem
    """

    file_changed: bool = False

    for tag, mapping  in self.tag_mappings.items():
      value = getattr(self, mapping["property"])
      file_value = TrackDetails.get_id3_value(self.id3, tag)

      if value:
        if file_value != value:
          # the current property has a value and it's different from the value in the file
          # self.frame_mapping[tag](encoding=3, text=value)
          self.id3[tag] = mapping["frame"](encoding=3, text=value)
          file_changed = True
      else:
        if file_value:
          # the current property doesn't have a value, but the file doesn't
          # pop is executed immediately, so file_changed doesn't need to be set
          self.id3.pop(tag, None)

    if file_changed:
      self.id3.save(self.file_path)

class TrackManager:
  SIMPLE_ARTIST_API_ENDPOINT = "api/artist"
  SIMPLE_ARTIST_ALIAS_API_ENDPOINT = "api/alias"
  SIMPLE_ARTIST_FRANCHISE_API_ENDPOINT = "api/franchise"
  MBARTIST_API_ENDPOINT = "api/mbartist"
  MBARTIST_API_PORT = 23409
  MBARTIST_API_DOMAIN = "localhost"

  def __init__(self):
    self.tracks: list[TrackDetails] = []
    self.artist_data: dict[MbArtistDetails] = {}

  async def load_directory(self, directory: str) -> None:
    """
    Gets all mp3 files in a directory and reads their id3 tags
    """
    self.directory = directory
    self.get_mp3_files()
    await self.read_file_metadata()

  def get_mp3_files(self) -> None:
    """
    Recursively gets a list of all mp3 files in the provided folder
    """
    for root, dirs, files in os.walk(self.directory):
      for file in files:
        if file.endswith(".mp3"):
          file_path = os.path.join(root, file)
          self.tracks.append(TrackDetails(file_path, self))
  
  async def save_files(self) -> None:
    """
    Saves changed id3 tags for all files in the local tracks list
    """

    loop = asyncio.get_event_loop()
    
    for track in self.tracks:
      if track.update_file == True:
        track.apply_custom_tag_values()

    await asyncio.gather(*(loop.run_in_executor(None, track.save_file_metadata) for track in self.tracks if track.update_file == True))

  async def read_file_metadata(self) -> None:
    """
    Reads ID3 tags for all files in the local tracks list
    """
    await asyncio.gather(*(track.read_file_metadata() for track in self.tracks))

  async def update_artists_info_from_db(self) -> None:
    """
    Update artist information from the database for all artists
    in the local artist_data list
    """

    for artist in self.artist_data.values():
      if isinstance(artist, SimpleArtistDetails):
        await TrackManager.update_simple_artist_from_db(artist)
      else:
        await TrackManager.update_mbartist_from_db(artist)

  @staticmethod
  async def update_simple_artist_from_db(artist: SimpleArtistDetails) -> None:
    """
    Loads customized artist and alias data for a simple artist from the database.
    """

    alias = await TrackManager.get_simple_artist_alias(artist.name, artist.product_id)
    if alias:
      artist.update_from_simple_artist_dict(alias[0])

  @staticmethod
  async def update_mbartist_from_db(artist: MbArtistDetails) -> None:
    """
    Loads customized artist data for an mb artist from the database.
    """

    mb_artist_details = await TrackManager.get_mbartist(artist.mbid)
    if mb_artist_details:
      artist.update_from_customization(mb_artist_details)

  async def create_artist_details_from_simple_artist_track(self, track: TrackDetails) -> list[SimpleArtistDetails]:
    """
    Reads track data to create a list of artist details, pushes it to the local artist_data list
    """

    if not hasattr(self, 'db_products') or not self.db_products:
      self.db_products = await TrackManager.list_simple_artist_franchise()
    
    returnObj: list[SimpleArtistDetails] = []

    product = SimpleArtistDetails.parse_simple_artist_franchise(track.product, track.album_artist, self.db_products)
    track.product = product["name"]
    artist_details = SimpleArtistDetails.parse_simple_artist(track.artist, product["name"], product["id"])

    for artist in artist_details:
      if artist.mbid not in self.artist_data:
        self.artist_data[artist.mbid] = artist

      returnObj.append(self.artist_data[artist.mbid])

    return returnObj
  
  def parse_mbartist_json(self, artist_relations_json: str) -> list[MbArtistDetails]:
    """
    Reads track data to create a list of artist details, pushes it to the local artist_data list
    """

    artist_details = MbArtistDetails.parse_json(artist_relations_json)
    returnObj: List[MbArtistDetails] = []
    for artist in artist_details:
      if artist.mbid not in self.artist_data:
        self.artist_data[artist.mbid] = artist

      returnObj.append(self.artist_data[artist.mbid])

    return returnObj

  async def send_changes_to_db(self) -> None:
    """
    Sends changes for all artists in the local artist_data list to the db
    """

    for artist in self.artist_data.values():
      if isinstance(artist, SimpleArtistDetails):
        if(artist.include != True):
          continue

        await TrackManager.send_simple_artist_changes_to_db(artist)
        await TrackManager.send_simple_artist_alias_changes_to_db(artist)
      else:
        await TrackManager.send_mbartist_changes_to_db(artist)

  @staticmethod
  async def send_mbartist_changes_to_db(artist: MbArtistDetails) -> None:
    """
    Sends changes for mb artist artist_data list to the db
    """

    existing_artist = await TrackManager.get_mbartist(artist.mbid)
    
    if (None == existing_artist):
      # DB doesn't have artist with the current MBID, create new DB artist
      await TrackManager.post_mbartist(artist)
      return
    
    artist.id = existing_artist["id"]

    if(existing_artist["include"] != artist.include or
        existing_artist["name"] != artist.custom_name or
        existing_artist["originalName"] != artist.custom_original_name):
      # artist with the current MBID was found in DB, but details were changed, update DB artist
      await TrackManager.update_mbartist(existing_artist["id"], artist)

    # Reaching this point means the DB artist is equal to the local artist, no actions need to be done

  @staticmethod
  async def send_simple_artist_changes_to_db(artist: SimpleArtistDetails) -> None:
    """
    Sends changes for simple artists to the db if it was changed
    """

    existing_artist = await TrackManager.get_simple_artist(None, artist.custom_name)
    if existing_artist:
      # if the artist is found in the DB by name, always update local artist ID to match the DB
      artist.id = existing_artist[0]["id"]
      return
    
    if not artist.id:
      # DB artist was not found by name and local data doesn't have ID, create new DB artist
      posted_artist = await TrackManager.post_simple_artist(artist)
      artist.id = posted_artist["id"]
      return
    
    # retrieve artist by ID to check for changed properties
    existing_artist_by_id = await TrackManager.get_simple_artist(artist.id, None)

    if existing_artist_by_id:
      existing_artist_by_id = existing_artist_by_id[0]

      if existing_artist_by_id["name"] == artist.custom_name:
        # local artist still matches DB artist, no action required
        return
    
      # local artist name has changed, update DB artist
      updated_artist = await TrackManager.update_simple_artist(existing_artist_by_id["id"], artist)
      artist.id = updated_artist["id"]
      return
    
    # If reaching this point, it means that the artist could not be not located 
    # in the DB via its name, and that it has an ID that doesn't exist in the DB
    # Ideally, this should never happen as it means that either the DB is
    # inconsistent or that there is a bug somewhere in the application
    raise ValueError(f"Artist with ID {artist.id} not found in database.")

  @staticmethod
  async def send_simple_artist_alias_changes_to_db(artist: SimpleArtistDetails) -> None:
    """
    Sends changes for simple artist aliases to the db if it was changed
    """

    existing_alias = await TrackManager.get_simple_artist_alias(artist.name, artist.product_id)
    
    if not existing_alias:
      # Alias doesn't exist, created
      await TrackManager.post_simple_artist_alias(artist.id, artist.name, artist.product_id)
      return

    if existing_alias:
      existing_alias = existing_alias[0]
      if existing_alias['artistId'] != artist.id:
        # Alias exists but points to the wrong artist, recreate it
        await TrackManager.delete_simple_artist_alias(existing_alias['id'])
        await TrackManager.post_simple_artist_alias(artist.id, artist.name, artist.product_id)

      # if no other conditions apply the alias already exists and is up to date, no action needs to be taken

  @staticmethod
  async def get_mbartist(mbid:str) -> dict:
    """
    Gets mb artist from the database
    """

    async with httpx.AsyncClient() as client:
      response = await client.get(f"http://{TrackManager.MBARTIST_API_DOMAIN}:{TrackManager.MBARTIST_API_PORT}/{TrackManager.MBARTIST_API_ENDPOINT}/mbid/{mbid}")
      
      match response.status_code:
        case 200:
          artist_info = response.json()
          return artist_info
        case 404:
          return None
        case _:
          raise Exception(f"Failed to fetch artist data for MBID {mbid}: {response.status_code}")

  @staticmethod
  async def list_simple_artist_franchise() -> dict:
    """
    Gets list of all franchise/product items from the db
    """

    endpoint = f"http://{TrackManager.MBARTIST_API_DOMAIN}:{TrackManager.MBARTIST_API_PORT}/{TrackManager.SIMPLE_ARTIST_FRANCHISE_API_ENDPOINT}"

    async with httpx.AsyncClient() as client:
      response = await client.get(f"{endpoint}")
      if response.status_code == 200:
        return response.json()
      else:
        return None

  @staticmethod
  async def get_simple_artist_franchise(name: str = None) -> dict:
    """
    Gets franchise/artist from the db
    """

    endpoint = f"http://{TrackManager.MBARTIST_API_DOMAIN}:{TrackManager.MBARTIST_API_PORT}/{TrackManager.SIMPLE_ARTIST_FRANCHISE_API_ENDPOINT}"

    if not name:
      raise ValueError("No parameters were provided to query.")

    async with httpx.AsyncClient() as client:
      response = await client.get(f"{endpoint}?name={name.replace(" ", "")}")
      if response.status_code == 200:
        return response.json()
      else:
        return None

  @staticmethod
  async def get_simple_artist(id:int, name:str) -> dict:
    """
    Gets details for a simple artist from the database
    """

    endpoint = f"http://{TrackManager.MBARTIST_API_DOMAIN}:{TrackManager.MBARTIST_API_PORT}/{TrackManager.SIMPLE_ARTIST_API_ENDPOINT}"
    params = {}

    if id:
      params['id'] = id
    if name:
      params['name'] = name
      
    if not params:
      raise ValueError("No parameters were provided to query.")
    
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])

    async with httpx.AsyncClient() as client:
      response = await client.get(f"{endpoint}?{query_string}")
      if response.status_code == 200:
        response_json = response.json()
        
        if response_json:
          return response_json

        return None
  
  @staticmethod
  async def get_simple_artist_alias(name: str = None, franchiseId: int = None) -> dict:
    """
    Gets all aliases of a simple artist from the db
    """

    endpoint = f"http://{TrackManager.MBARTIST_API_DOMAIN}:{TrackManager.MBARTIST_API_PORT}/{TrackManager.SIMPLE_ARTIST_ALIAS_API_ENDPOINT}"
    params = {}

    if name:
      params['name'] = name.replace(" ", "")
    if franchiseId:
      params['franchiseId'] = franchiseId

    if not params:
      raise ValueError("No parameters were provided to query.")
    
    query_string = "&".join([f"{key}={value}" for key, value in params.items()])

    async with httpx.AsyncClient() as client:
      response = await client.get(f"{endpoint}?{query_string}")
      if response.status_code == 200:
        response_json = response.json()
        
        if response_json:
          return response_json

        return None

  @staticmethod
  async def post_mbartist(artist:MbArtistDetails) -> None:
    """
    Creates a new mb artist in the db from an artist details object
    """
    
    endpoint = f"http://{TrackManager.MBARTIST_API_DOMAIN}:{TrackManager.MBARTIST_API_PORT}/{TrackManager.MBARTIST_API_ENDPOINT}"

    data = {
      "MbId": artist.mbid,
      "Name": artist.custom_name,
      "OriginalName": artist.custom_original_name,
      "Include": artist.include
    }

    async with httpx.AsyncClient() as client:
      response = await client.post(endpoint, json=data)

      if response.is_success:
        return
      
      match response.status_code:
        case 409:
          raise Exception(f"Artist with MBID {artist.mbid} already exists in DB: {response.text} ({response.status_code} {response.reason_phrase})")
        case _:
          raise Exception(f"Failed to create artist with MBID {artist.mbid}: {response.text} ({response.status_code} {response.reason_phrase})")
  
  @staticmethod
  async def post_simple_artist(artist:SimpleArtistDetails) -> dict:
    """
    Creates a new simple artist in the db from an artist details object
    """

    endpoint = f"http://{TrackManager.MBARTIST_API_DOMAIN}:{TrackManager.MBARTIST_API_PORT}/{TrackManager.SIMPLE_ARTIST_API_ENDPOINT}"

    data = {
      "Name": artist.custom_name
    }

    async with httpx.AsyncClient() as client:
      response = await client.post(endpoint, json=data)

      if response.is_success:
        return response.json()
      
      match response.status_code:
        case 409:
          raise Exception(f"Failed to post artist data for MBID {artist.mbid}: {response.text} ({response.status_code} {response.reason_phrase})")
        case _:
          raise Exception(f"Failed to post artist data for MBID {artist.mbid}: {response.text} ({response.status_code} {response.reason_phrase})")
  
  @staticmethod
  async def post_simple_artist_alias(artist_id: int, name: str, franchise_id: int) -> None:
    """
    Creates a new alias for a simple artist in the db
    """

    endpoint = f"http://{TrackManager.MBARTIST_API_DOMAIN}:{TrackManager.MBARTIST_API_PORT}/{TrackManager.SIMPLE_ARTIST_ALIAS_API_ENDPOINT}"
    
    data = {
      "Name": name.replace(" ", ""),
      "artistid": artist_id,
      "franchiseid": franchise_id
    }
    
    async with httpx.AsyncClient() as client:
      response = await client.post(endpoint, json=data)
      
      if response.is_success:
        return
      
      match response.status_code:
        case 409:
          raise Exception(f"Alias with name {name} already exists in DB: {response.text} ({response.status_code} {response.reason_phrase})")
        case _:
          raise Exception(f"Failed to create alias for name {name}: {response.text} ({response.status_code} {response.reason_phrase})")

  @staticmethod
  async def delete_simple_artist_alias(id: int) -> None:
    """
    Deletes a simple artist alias
    """

    async with httpx.AsyncClient() as client:
      response = await client.delete(f"http://{TrackManager.MBARTIST_API_DOMAIN}:{TrackManager.MBARTIST_API_PORT}/{TrackManager.SIMPLE_ARTIST_ALIAS_API_ENDPOINT}/id/{id}")
      
      match response.status_code:
        case 200:
          return 
        case 404:
          raise Exception(f"Alias with ID {id} was not found: {response.status_code}")
        case _:
          raise Exception(f"An error occurred when deleting alias with ID {id}: {response.status_code}")

  @staticmethod
  async def update_mbartist(id:int, artist:MbArtistDetails) -> None:
    """
    Updates the db record of a mb artist
    """

    endpoint = f"http://{TrackManager.MBARTIST_API_DOMAIN}:{TrackManager.MBARTIST_API_PORT}/{TrackManager.MBARTIST_API_ENDPOINT}/id"

    data = {
      "MbId": artist.mbid,
      "Name": artist.custom_name,
      "OriginalName": artist.custom_original_name,
      "Include": artist.include
    }

    async with httpx.AsyncClient() as client:
      response = await client.put(f"{endpoint}/{id}", json=data)

      if response.is_success:
        return response.json()
      
      match response.status_code:
        case 404:
          raise Exception(f"Could not find artist with MBID {artist.mbid}: {response.text} ({response.status_code} {response.reason_phrase})")
        case _:
          raise Exception(f"Failed to update artist data for MBID {artist.mbid}: {response.text} ({response.status_code} {response.reason_phrase})")

  @staticmethod
  async def update_simple_artist(id:int, artist:SimpleArtistDetails) -> None:
    """
    Updates the db record of a simple artist
    """

    endpoint = f"http://{TrackManager.MBARTIST_API_DOMAIN}:{TrackManager.MBARTIST_API_PORT}/{TrackManager.SIMPLE_ARTIST_API_ENDPOINT}/id"

    data = {
      "Name": artist.custom_name
    }

    async with httpx.AsyncClient() as client:
      response = await client.put(f"{endpoint}/{id}", json=data)

      if response.is_success:
        return response.json()
      
      match response.status_code:
        case 404:
          raise Exception(f"Could not find artist with MBID {artist.id}: {response.text} ({response.status_code} {response.reason_phrase})")
        case _:
          raise Exception(f"Failed to update artist data for MBID {artist.mbid}: {response.text} ({response.status_code} {response.reason_phrase})")


async def seedData() -> None:

  data = {
    "MbId": "f3688ad9-cd14-4cee-8fa0-0f4434e762bb",
    "Name": "ClariS-ChangedX2",
    "OriginalName": "ClariS-Original-ChangedX2",
    "Include": True
  }
  # dde = await send_get_request("http://localhost:23409/api/mbartist/mbid/f3688ad9-cd14-4cee-8fa0-0f4434e762bb")
  # dde = await send_post_request(data, "http://localhost:23409/api/mbartist")
  
  # dde = await send_get_request("http://localhost:23409/api/mbartist/mbid/f3688ad9-cd14-4cee-8fa0-0f4434e762bb")
  dde = await send_put_request(data, "http://localhost:23409/api/mbartist/id/1")

  data = {
    "Name": "_",
  }
  await send_post_request(data, "http://localhost:23409/api/franchise")
  product_default = await send_get_request(f"http://localhost:23409/api/franchise?name={data["Name"]}")

  data = {
    "Name": "TestFranchise1",
  }
  await send_post_request(data, "http://localhost:23409/api/franchise")
  product_testfranchise1 = await send_get_request(f"http://localhost:23409/api/franchise?name={data["Name"]}")

  data = {
    "Name": "TestFranchise2",
  }
  await send_post_request(data, "http://localhost:23409/api/franchise")
  product_testfranchise2 = await send_get_request(f"http://localhost:23409/api/franchise?name={data["Name"]}")

  data = {
    "Name": "idolmaster",
  }
  await send_post_request(data, "http://localhost:23409/api/franchise")
  product_idolmasterproduct = await send_get_request(f"http://localhost:23409/api/franchise?name={data["Name"]}")

  data = {
    "Name": "sandorionSERVER",
  }

  await send_post_request(data, "http://localhost:23409/api/artist")
  artist_sandrion = await send_get_request(f"http://localhost:23409/api/artist?name={data["Name"]}")

  data = {
    "artistId": artist_sandrion["id"],
    "Name": "サンドリオン",
    "franchiseId": product_default["id"],
  }
  artist_sandrionimas = await send_post_request(data, "http://localhost:23409/api/alias")


  data = {
    "Name": "sandorionSERVERIMAS",
  }
  # artist_sandrionimas = await send_get_request(f"http://localhost:23409/api/artist?name={data["Name"]}")
  # await send_post_request(data, "http://localhost:23409/api/artist")
  artist_sandrionimas = await send_get_request(f"http://localhost:23409/api/artist?name={data["Name"]}")
  # await send_post_request(data, "http://localhost:23409/api/artist")

  data = {
    "artistId": artist_sandrionimas["id"],
    "Name": "サンドリオン",
    "franchiseId": product_idolmasterproduct["id"],
  }
  # await send_get_request(f"http://localhost:23409/api/alias?name={data["Name"]}&franchiseId={data["franchiseId"]}")
  artist_sandrionimas = await send_post_request(data, "http://localhost:23409/api/alias")
  await send_get_request(f"http://localhost:23409/api/alias?name={data["Name"]}&franchiseId={data["franchiseId"]}")
  artist_sandrionimas = await send_post_request(data, "http://localhost:23409/api/alias")


async def send_post_request(data, url) -> None:
  async with httpx.AsyncClient() as client:
    response = await client.post(url, json=data)
    print('url:', url)
    print('Status Code:', response.status_code)
    print('Response:', response.text)

async def send_get_request(url) -> None:
  async with httpx.AsyncClient() as client:
    response = await client.get(url)
    print('url:', url)
    print('Status Code:', response.status_code)
    print('Response:', response.text)
    a = (response.json())[0]
    return a

async def send_put_request(data, url) -> None:
  async with httpx.AsyncClient() as client:
    response = await client.put(url, json=data)
    print('url:', url)
    print('Status Code:', response.status_code)
    print('Response:', response.text)

async def main() -> None:
  # await seedData()
  manager = TrackManager()
  dir = "C:/Users/email_000/Desktop/music/sample/nodetailsmultiple"
  dir = "C:/Users/email_000/Desktop/music/sample/detailsmultiple"
  dir = "C:/Users/email_000/Desktop/music/sample/recall"
  dir = "C:/Users/email_000/Desktop/music/sample/nodetails2"
  dir = "C:/Users/email_000/Desktop/music/sample/spiceandwolf"
  dir = "C:/Users/email_000/Desktop/music/check/[2024.05.16] 学園アイドルマスター 初星学園 [MP3 320K]/clumsy trick"
  await manager.load_directory(dir)
  await manager.update_artists_info_from_db()
  # await manager.send_changes_to_db()
  # await manager.save_files()

if __name__ == "__main__":
  asyncio.run(main())


# GET api/artist, item exists -> http 200, response text = `[{"id":99,"name":"ARTISTNAME","aliases":[]}]`
# GET api/artist, item does not exist -> http 200, response text = `[]`

# POST api/artist, item already exists -> http 409
# POST api/artist, item does not exist -> http 200, response text = `{"id":99,"name":"ARTISTNAME","aliases":[]}`

# GET api/alias, item exists -> http 200, resonse text = `'[{"id":88,"name":"ALIASNAME","artistId":99,"artist":"ARTISTNAME","franchiseId":4,"franchise":"FRANCHISENAME"}]'`
# GET api/alias, item does not exist -> http 200, response text = `[]`

# POST api/alias, item already exists -> http 409
# POST api/alias, item does not exist -> http 200, response text = `{"id":88,"name":"ALIASNAME","artistId":99,"artist":"ARTISTNAME","franchiseId":4,"franchise":"FRANCHISENAME"}`

# DELETE api/alias, item exists -> http 200
# DELETE api/alias, item doesn't exist -> http 404

# GET api/mbartist/mbid, item exists -> http 200, `{'id': 1, 'mbId': 'MBID', 'name': 'ARTISTNAME', 'originalName': 'ORIGINALNAME', 'include': INCLUDE}`
# GET api/mbartist/mbid, item does not exist -> http 404

# POST api/mbartist, item exists -> http 409
# POST api/mbartist, item does not exist -> http 200, `{'id': 1, 'mbId': 'MBID', 'name': 'ARTISTNAME', 'originalName': 'ORIGINALNAME', 'include': INCLUDE}`

# PUT api/mbartist/id, item exists -> http 200, `{'id': 1, 'mbId': 'MBID', 'name': 'ARTISTNAME', 'originalName': 'ORIGINALNAME', 'include': INCLUDE}`
# PUT api/mbartist/id, item does not exist -> http 404