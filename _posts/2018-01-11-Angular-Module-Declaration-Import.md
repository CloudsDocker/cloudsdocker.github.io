---
title: What is difference between declarations, providers and import in NgModule
tags:
- Angular
- JavaScript
- NodeJs
layout: posts
---

# What is difference between declarations, providers and import in NgModule 

- imports: is used to import supporting modules likes FormsModule, RouterModule, CommonModule, or any other custom-made feature module. makes the exported declarations of other modules available in the current module
- declarations are to make directives (including components and pipes) from the current module available to other directives in the current module. Selectors of directives, components or pipes are only matched against the HTML if they are declared or imported. declaration is used to declare components, directives, pipes that belongs to the current module. Everything inside declarations knows each other. For example, if we have a component, say UsernameComponent, which display list of the usernames, and we also have a pipe, say toupperPipe, which transform string to uppercase letter string. Now If we want to show usernames in uppercase letters in our UsernameComponent, we can use the toupperPipe which we had created before but how UsernameComponent know that the toupperPipe exist and how we can access and use it, here comes the declarations, we can declare UsernameComponent and toupperPipe.
- providers are to make services and values known to DI. They are added to the root scope and they are injected to other services or directives that have them as dependency.provider is used to inject the services required by components, directives, pipes in our module.
