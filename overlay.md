
# Canonn Overlay Configuration

The canonn overlay allows a multitude of options in order to customize the overlay look and behavior. This can be controlled by editing [overlay.json](../../canonn/overlay.json). The file supplied with the build is copied to the [canonn configuration directory](../../canonn) and the copy can be edited without being overwritten by subsequent releases. 

The [overlay.json](../../canonn/overlay.json) file is loaded when the plugin starts and provides information on how to display the overlay on your screen.

**After any edit to this file, restart the plugin to have the changes appear**

It's structure should look like this:
```json
{
  "types":{
      
    },
  
  "positions":{
      
    },
    
  "codex-ignore-list":[
        
    ]
}
```


## Types

The types section describes each of the different type of overlay that can be displayed, each type of overlay should be in this list.
The object should look like this:
```json
 "Name of the type":{
            "enabled":true,
            "position":"top-middle",            
            "color":"#FFFFFF",
            "display_time":10,
            "max_size":60,
            "header_spacing":45,
            "line_spacing":20,
            "header":{
                "text":"Header text",
                "color":"#EE4220"
            }
}
```

You can modify all of these parameters:

| Parameter name | Value                                                | Description                                                                                                      |
|----------------|------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| `enabled`        | true/false                                           | Will override any other parameter and decide wether or not this type of overlay will be displayed                |
| `position`       | "left-top"/"top-middle"/"right-middle"/"left-middle" | Decides on wich position the text should appear, positions are explained in the "positions" section              |
| `color`          | Color in #rrggbb format, ex: #FFFFFF                 | The text color for the overlay                                                                                   |
| `display_time`   | Time in seconds, ex:13                               | The time the overlay is displayed on the screen in seconds                                                       |
| `max_size`       | Characters, ex:60                                    | The max character per line on the overlay text, if the size is exceeded the text will be displayed on a new line |
| `header_spacing` | Size in px, ex: 45                                   | The space in pixels between the header text and the text                                                         |
| `line_spacing`   | Size in px, ex: 20                                   | The space between two lines in the text                                                                          |
| `header.text`    | Text, ex: "New POI"                                  | The text in the header, this text is sometimes concatenated with the distance                                    |
| `header.color`   | Color in ##rrggbb format, ex: #FFFFFF                | The header text color    |

Use websites such as [RapidTables](https://www.rapidtables.com/web/color/RGB_Color.html) to get #rrggbb colors

## Positions

The positions section describe the different positions used by the different types in their `position` parameter, you can add a new position by adding a new object in this section and then refer it in the `position` parameter of the type you want to change the position of.

Position structure:
```json
"position name":{
  "x":100,
  "y":100
}
```

The `x`and `y` parameters describe coordinates in pixel on a 1920 by 1080 screen
