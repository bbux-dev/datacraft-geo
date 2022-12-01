datacraft-geo
===============

Custom plugin for [datacraft](https://datacraft.readthedocs.io/en/latest) to extend the geo types to include
`geo.mgrs` and `geo.utm`

## Usage in Specs

### `geo.mgrs`

```json
{
  "mgrs":{
    "type": "geo.mgrs"
  }
}
```

```shell
$ datacraft -s geo.mgrs.json -i 4 -r 1 --format json -x -l error
{"mgrs": "33TVE8831137089"}
{"mgrs": "28CET4236233893"}
{"mgrs": "33RXH7235656683"}
{"mgrs": "44XNJ6899271743"}
```

### `geo.utm`

```json
{
  "utm":{
    "type": "geo.utm"
  }
}
```

```shell
$ datacraft -s geo.utm.json -i 3 -r 1 --format json -x -l warning

{"utm": "37 T 482637 5257154"}
{"utm": "38 T 489869 4504951"}
{"utm": "33 K 673513 7460351"}
{"utm": "20 Q 629432 1992725"}
```

#### Customizing UTM output

We use the utm package under the hood, which provides it's output as a tuple of
(EASTING, NORTHING, ZONE_NUMBER, ZONE_LETTER) e.g: (513864.9288961077, 1664402.2459186069, 25, "P").
The default is to format this as:
`{{ zone_number }} {{ zone_letter }} {{ easting | int }} {{ northing | int }}` You can override this by specifying 
a `template` config parameter with the fields arranged as you like.  See example below. The other way is to override
the `geo_utm_template` default value from the command line
(`datacraft --set-defaults geo_utm_template="{{ zone_number }}{{ zone_letter }} {{ easting | int }}/{{ northing | int }
}"`). Note that `{{ zn }}` can be used in place of zone_number and `{{ zl }}` in place of zone_letter.


```json
{
  "utm_custom":{
    "type": "geo.utm",
    "config": {
      "template": "{{ zn }}{{ zl }} {{ easting | int }}/{{ northing | int }}"
    }
  }
}
```

```shell
$ datacraft -s geo.utm.custom.json -i 3 -r 1 --format json -x -l warning
{"utm_custom": "37T 325263/5115949"}
{"utm_custom": "31N 676324/553043"}
{"utm_custom": "45J 300889/6854467"}
{"utm_custom": "44R 288307/2890462"}
```
