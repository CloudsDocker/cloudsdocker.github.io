# This is website based on `hugo`

## run hugo server locally

```bash
hugo server -D
```

## Build static website

```bash
hugo -D
```

They will generate static pages and output to folder `public`

## To deploy website to S3

Run below command to generate and deploy to S3
```bash
hugo deploy --maxDeletes -1
```