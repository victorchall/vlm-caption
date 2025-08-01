## Prompt tuning

A core intuition and opinion baked into the design of VLM Caption is that multi-turn conversation can help extract superior information by allowing different questions to be asked, then bring them together with a final summary request.  Other VLM scripts or apps are likely just trying to "one shot" a caption or description, but the quality and detail of these results are limited by the models one-shot capabilities.

Prompt tuning can help direct the model to detail the things that you feel are most important along with following a certain style of captioning. 

Prompt tuning and results may depend a lot on what model you use.  Largely models like Gemma3 27B and Llama4 Scout are more likely to be "steerable" and generally more intelligent, but most modern VLMS today are basedon pretrained LLM models (often Llama2 or Llama3) with vision projectors attached, and they retain their normal LLM-like instruct abilities so prompt tuning can really impact output.  Just keep in mind a system prompt and series of prompts that works well on one model may perform worse on another model.  It's best to pick the best model you can run on your hardware first, stick with it, and tune your prompts.

The example prompt chain included should give you some good ideas. Note that 2 to 5 is generally sufficient, and too many may lead to worse outcomes depending on the model used, and increased VRAM usage. 

You can also create different prompt series for different projects.  Captioning a bunch of images that are purely landscape? Purely human subject?  Taking some time to tune prompts for each will improve results and help capture the types of details you feel are important.

Here's an example prompt series if you know the *images are primary of single human/character subjects* and want to gather certain information about framing, outfits, and pose:

1. For this query answer briefly.  What is the central focus of the image?  Is it a close up of a particular body part? Also, What is the framing of the image?  Examples would be full shot if a person's entire body is visible, medium shot if their upper body is visible, close up for shoulders and face, or an over-the-shoulder shot if someone's shoulder or back of their head is visible on one side.  Finally, is the image at a low angle looking up or looking down from below in a high angle shot?
2. Describe the outfit in detail. 
3. Describe the pose in simple terms, such as sitting, standing, leaning back, etc.  Are legs crossed, straight, or in a particular pose?  Where are their hands placed?
4. To finalize, summarize the description of the image in four to five sentences, focusing on factual statements about the image. Do not include any markdown, headers, or special formatting. Do not start with 'the image depicts' or similar.  Simply exclude such phrases and focus on what IS visible.

**Most importantly, the final prompt needs to be a request for a summary.** This requirement is baked into the applications design because only the final prompt's response is saved.

Similarly, if you know your entire dataset to be captioned is from a specific source, like "screenshots of Final Fantasy VII Rebirth" you can tell the model in the final summary request prompt to always include that.  

## System Prompt

Try giving example summaries in the system prompt. *The second paragraph assumes the File Path hint is being used, and the images to be captioned are organized accordingly. You'd remove that paragraph if you did not do such presorting activities.*

      You are an production assistant tasked with writing detaled captions for images of Final Fantasy VII Rebirth that will be posted online. 

      The folder and filename of the image will be provided. The directory will the name of the video game and the filename will also include the name of the character and that information can be trusted to be accurate.

      You will be asked a series questions about the image and finally asked to summarize.  For summaries, do not discuss the prior examination or or analysis process/questions.  Here are examples of good summaries:

      "Close up of Cloud Strife facing slightly to the left. He has spikey blonde hair, blue eyes, and a neutral expression. He wears a dark blue, sleeveless cloth top and has a dark metallic spaulder on his left shoulder with bolts protruding from it. Screenshot from Final Fantasy VII Rebirth."

      "Aerith Gainsborough is shown in a wide shot as she stands on a grassy hill near a wooden fence. She wears a red cropped jacket over a long, light-pink dress.  Her right hand rests on a large yellow Chocobo which stands near her to the left, wearing a saddle and harness. A red barn can be seen in the background on the right, and a dirt path next to the fence line.  The sky is clear and the scene is brightly lit by natural light.  Screenshot from Final Fantasy VII Rebirth."

      "... yet another example..."

      "... yet another example..."

      "... yet another example..."

      These examples provide clear descriptions and summarizations of the character, outfit, composition, and surroundings while avoiding narrative context or unwanted discussions of what might be visible or not. Your summarizations should be based on the results of the examination, but can follow a similar form and structure as these examples, starting with the main subject, framing, outfit details, scene details, and finally a brief description of the general scene and backdrop along with the "Screenshot from Final Fantasy VII Rebirth" at the end.

The [metadata hint source system](HINTSOURCES.md) works quite well without mentioning "metadata" in your prompts, but mentioning metadata in the system prompt may improve the likelihood it is used by the model to inform its captioning.  You can also mention in the system prompt that "*metadata" can be trust to be accurate*" if you are confident about the metadata.