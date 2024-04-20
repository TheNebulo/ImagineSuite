import openai, asyncio, requests

def run_async_as_sync(async_function):
    return asyncio.get_event_loop().run_until_complete(async_function)

def verify_openai(api_key):
    client = openai.OpenAI(api_key=api_key)
    try: client.embeddings.create(input="", model="text-embedding-3-small")
    except openai.APIConnectionError as e: return "network"
    except: return "invalid"
    else: return "valid"

def generate_dalle3(prompt, batches, additional_parameters):
    
    response_format = "b64_json"
    
    client = openai.AsyncOpenAI(api_key=SERVICES["OPENAI"]["api_key"])
    if additional_parameters['aspect_ratio']['value'] == "square": additional_parameters['aspect_ratio']['value'] = "1024x1024"
    if additional_parameters['aspect_ratio']['value'] == "landscape": additional_parameters['aspect_ratio']['value'] = "1792x1024"
    if additional_parameters['aspect_ratio']['value'] == "portrait": additional_parameters['aspect_ratio']['value'] = "1024x1792"
    
    for i, batch in enumerate(batches):
        yield {"message": f"Generating batch #{i+1} with {batch} image(s)...", "value":None, "type":"log", "level":None}
        
        async def get_image(prompt, size, quality, style, response_format = "b64_json"):
            response = await client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                style=style,
                response_format=response_format,
                n=1
            )
            if response_format == "url": image = response.data[0].url
            else: image = response.data[0].b64_json
            return image

        tasks = [get_image(prompt, additional_parameters['aspect_ratio']['value'], additional_parameters['quality']['value'], additional_parameters['style']['value'], response_format=response_format) for _ in range(batch)]
        try: images = run_async_as_sync(asyncio.gather(*tasks))
        except openai.AuthenticationError as e:
            yield {"message": f"The API key for OpenAI is incorrect.", "value":e, "type":"error", "level":"critical"}
        except openai.BadRequestError as e:
            yield {"message": f"Provided prompt was rejected by OpenAI.", "value":e, "type":"error", "level":"critical"}
        except openai.RateLimitError as e:
            if "quota" in e.message:
                yield {"message": f"Your OpenAI account does not have sufficient credits/balance.", "value":e, "type":"error", "level":"critical"}
            else:
                yield {"message": f"Too many requests sent to OpenAI. Please wait and try again later.", "value":e, "type":"error", "level":"warn"}
        except Exception as e:
            yield {"message": "Unknown error.", "value":e, "type":"error", "level":"warn"}
        else:
            yield {"message": f"Successfully generated batch #{i+1}!", "value": images, "type":response_format, "level": None}
            
def generate_dalle2(prompt, batches, additional_parameters):
    
    response_format = "b64_json"
    
    client = openai.AsyncOpenAI(api_key=SERVICES["OPENAI"]["api_key"])
    
    for i, batch in enumerate(batches):
        yield {"message": f"Generating batch #{i+1} with {batch} image(s)...", "value":None, "type":"log", "level":None}
        
        async def get_image(prompt, response_format = "b64_json"):
            response = await client.images.generate(
                model="dall-e-2",
                prompt=prompt,
                size="1024x1024",
                response_format=response_format
            )
            if response_format == "url": image = response.data[0].url
            else: image = response.data[0].b64_json
            return image

        tasks = [get_image(prompt, response_format=response_format) for _ in range(batch)]
        try: images = run_async_as_sync(asyncio.gather(*tasks))
        except openai.AuthenticationError as e:
            yield {"message": f"The API key for OpenAI is incorrect.", "value":e, "type":"error", "level":"critical"}
        except openai.BadRequestError as e:
            yield {"message": f"Provided prompt was rejected by OpenAI.", "value":e, "type":"error", "level":"critical"}
        except openai.RateLimitError as e:
            if "quota" in e.message:
                yield {"message": f"Your OpenAI account does not have sufficient credits/balance.", "value":e, "type":"error", "level":"critical"}
            else:
                yield {"message": f"Too many requests sent to OpenAI. Please wait and try again later.", "value":e, "type":"error", "level":"warn"}
        except Exception as e:
            yield {"message": "Unknown error.", "value":e, "type":"error", "level":"warn"}
        else:
            yield {"message": f"Successfully generated batch #{i+1}!", "value": images, "type":response_format, "level": None}
            
def generate_sd3(prompt, batches, additional_parameters):
    def generate_image(prompt, api_key, aspect_ratio):
        response = requests.post(
            f"https://api.stability.ai/v2beta/stable-image/generate/sd3",
            headers={
                "authorization": f"Bearer {api_key}",
                "accept": "application/json"
            },
            files={"none": ''},
            data={
                "prompt": prompt,
                "model": "sd3",
                "output_format": "png",
                "aspect_ratio": aspect_ratio
            },
        )
        if response.status_code == 200: return response.json()["image"]
        else: raise Exception(response.status_code)

    async def get_image(prompt, api_key, aspect_ratio):
        loop = asyncio.get_event_loop()
        image = loop.run_in_executor(None, generate_image, prompt, api_key, aspect_ratio)
        return await image
    
    for i, batch in enumerate(batches):
        yield {"message": f"Generating batch #{i+1} with {batch} image(s)...", "value":None, "type":"log", "level":None}
        tasks = [get_image(prompt, SERVICES["STABILITYAI"]["api_key"], additional_parameters['aspect_ratio']['value'] ) for _ in range(batch)]
        
        try: 
            images = run_async_as_sync(asyncio.gather(*tasks))
        except Exception as e:
            status_code = int(str(e))
            if status_code == 401:
              yield {"message": f"The API key for StabilityAI is incorrect.", "value":e, "type":"error", "level":"critical"}  
            elif status_code == 402:
                yield {"message": f"Your OpenAI account does not have sufficient credits/balance.", "value":e, "type":"error", "level":"critical"}
            elif status_code == 403:
                yield {"message": f"Provided prompt was rejected by StabilityAI.", "value":e, "type":"error", "level":"critical"}
            elif status_code == 429:
                yield {"message": f"Too many requests sent to StabilityAI. Please wait and try again later.", "value":e, "type":"error", "level":"warn"}
            elif status_code == 500:
                yield {"message": f"StabilityAI faced an unexpected error.", "value":e, "type":"error", "level":"warn"}
            else:
                yield {"message": f"Unknown error.", "value":e, "type":"error", "level":"warn"}
        else:
            yield {"message": f"Successfully generated batch #{i+1}!", "value": images, "type":"b64_json", "level": None}
            
def generate_sd3_turbo(prompt, batches, additional_parameters):
    def generate_image(prompt, api_key, aspect_ratio):
        response = requests.post(
            f"https://api.stability.ai/v2beta/stable-image/generate/sd3",
            headers={
                "authorization": f"Bearer {api_key}",
                "accept": "application/json"
            },
            files={"none": ''},
            data={
                "prompt": prompt,
                "model": "sd3-turbo",
                "output_format": "png",
                "aspect_ratio": aspect_ratio
            },
        )
        if response.status_code == 200: return response.json()["image"]
        else: raise Exception(response.status_code)

    async def get_image(prompt, api_key, aspect_ratio):
        loop = asyncio.get_event_loop()
        image = loop.run_in_executor(None, generate_image, prompt, api_key, aspect_ratio)
        return await image
    
    for i, batch in enumerate(batches):
        yield {"message": f"Generating batch #{i+1} with {batch} image(s)...", "value":None, "type":"log", "level":None}
        tasks = [get_image(prompt, SERVICES["STABILITYAI"]["api_key"], additional_parameters['aspect_ratio']['value'] ) for _ in range(batch)]
        
        try: 
            images = run_async_as_sync(asyncio.gather(*tasks))
        except Exception as e:
            status_code = int(str(e))
            if status_code == 401:
              yield {"message": f"The API key for StabilityAI is incorrect.", "value":e, "type":"error", "level":"critical"}  
            elif status_code == 402:
                yield {"message": f"Your OpenAI account does not have sufficient credits/balance.", "value":e, "type":"error", "level":"critical"}
            elif status_code == 403:
                yield {"message": f"Provided prompt was rejected by StabilityAI.", "value":e, "type":"error", "level":"critical"}
            elif status_code == 429:
                yield {"message": f"Too many requests sent to StabilityAI. Please wait and try again later.", "value":e, "type":"error", "level":"warn"}
            elif status_code == 500:
                yield {"message": f"StabilityAI faced an unexpected error.", "value":e, "type":"error", "level":"warn"}
            else:
                yield {"message": f"Unknown error.", "value":e, "type":"error", "level":"warn"}
        else:
            yield {"message": f"Successfully generated batch #{i+1}!", "value": images, "type":"b64_json", "level": None}
            
SERVICES = {
    "OPENAI" : {
        "api_key" : None,
        "required" : False,
        "alias" : "OpenAI",
        "description" : "The [bold]OpenAI[/bold] platform providing Dall-E 2 and 3.",
        "link" : "https://platform.openai.com/api-keys",
        "models" : [
            {
                "name" : "dalle-3",
                "alias" : "Dall-E 3",
                "online_only" : True,
                "description" : "(Recommended) OpenAI's flagship image generator that trades affordability for a wide array of generation features.",
                "additional_parameters" : [
                    {"name" : "aspect_ratio", "alias" : "Aspect Ratio", "description" : "The aspect ratio/format of the generated image(s).", "default" : "square", "options" : ["square", "landscape", "portrait"]},
                    {"name" : "quality", "alias" : "Quality", "description" : "The quality of the image. Affects attention to detail, not resolution.", "default" : "standard", "options" : ["hd", "standard"]},
                    {"name" : "style", "alias" : "Style", "description" : "The style of the image. Vivid images are more dramatic and hyper-real than natural images.", "default" : "vivid", "options" : ["vivid", "natural"]}
                ],
                "generate_function" : generate_dalle3
            },
            {
                "name" : "dalle-2",
                "alias" : "Dall-E 2",
                "online_only" : True,
                "description" : "An older image generator that provides faster and cheaper but lower quality image generation.",
                "additional_parameters" : None,
                "generate_function" : generate_dalle2
            },
        ],
        "always_verify" : False,
        "verification_function" : verify_openai
    },
    "STABILITYAI" : {
        "api_key" : None,
        "required" : False,
        "alias" : "StabilityAI",
        "description" : "The [bold]StabilityAI[/bold] platform providing Stable Diffusion 3 and 3 Turbo.",
        "link" : "https://platform.stability.ai/account/keys",
        "models" : [
            {
                "name" : "sd3",
                "alias" : "Stable Diffusion 3",
                "online_only" : True,
                "description" : "(Recommended) The newest image generator from StabilityAI.",
                "additional_parameters" : [{"name" : "aspect_ratio", "alias" : "Aspect Ratio", "description" : "The aspect ratio/format of the generated image(s).", "default" : "1:1", "options" : ["16:9","1:1","21:9","2:3","3:2", "4:5", "5:4", "9:16", "9:21"]}],
                "generate_function" : generate_sd3
            },
            {
                "name" : "sd3-turbo",
                "alias" : "Stable Diffusion 3 Turbo",
                "online_only" : True,
                "description" : "A faster and cheaper version of Stable Diffusion 3",
                "additional_parameters" : [{"name" : "aspect_ratio", "alias" : "Aspect Ratio", "description" : "The aspect ratio/format of the generated image(s).", "default" : "1:1", "options" : ["16:9","1:1","21:9","2:3","3:2", "4:5", "5:4", "9:16", "9:21"]}],
                "generate_function" : generate_sd3_turbo
            },
        ],
        "always_verify" : False,
        "verification_function" : None
    }
}