---
title: Router in angular
---

```javascript
const appRoutes: Routes = [
  { path: 'crisis-center', component: CrisisListComponent },
  { path: 'hero/:id',      component: HeroDetailComponent },
  {
    path: 'heroes',
    component: HeroListComponent,
    data: { title: 'Heroes List' }
  },
  { path: '',
    redirectTo: '/heroes',
    pathMatch: 'full'
  },
  { path: '**', component: PageNotFoundComponent }
];

@NgModule({
  imports: [
    RouterModule.forRoot(
      appRoutes,
      { enableTracing: true } // <-- debugging purposes only
    )
    // other imports here
  ],
  ...
})
export class AppModule { }
```

- The data property in the third route is a place to store arbitrary data associated with this specific route. The data property is accessible within each activated route. Use it to store items such as page titles, breadcrumb text, and other read-only, static data. You'll use the resolve guard to retrieve dynamic data
- The empty path in the fourth route represents the default path for the application, the place to go when the path in the URL is empty, as it typically is at the start. This default route redirects to the route for the /heroes URL and, therefore, will display the HeroesListComponent.
- The ** path in the last route is a wildcard. The router will select this route if the requested URL doesn't match any paths for routes defined earlier in the configuration. This is useful for displaying a "404 - Not Found" page or redirecting to another route.
- The order of the routes in the configuration matters and this is by design. The router uses a **first-match wins strategy** when matching routes, so **more specific routes should be placed above less specific routes**. 

## Router outlet

The router matches that URL to the route path  and displays the Component after a RouterOutlet that you've placed in the host view's HTML.

```javascript
content_copy
<router-outlet></router-outlet>
<!-- Routed views go here -->
```

## Define routes
A router must be configured with a list of route definitions.

## mechanism
- When the application requests navigation to the path /crisis-center, the router activates an instance of CrisisListComponent, displays its view, and updates the browser's address location and history with the URL for that path.
- Pass the array of routes, appRoutes, to the RouterModule.forRoot method. It returns a module, containing the configured Router service provider, plus other providers that the routing library requires. Once the application is bootstrapped, the Router performs the initial navigation based on the current browser URL

## Some key points of setting up router
- Load the router library.
- Add a nav bar to the shell template with anchor tags, routerLink and routerLinkActive directives.
- Add a router-outlet to the shell template where views will be displayed.
- Configure the router module with RouterModule.forRoot.
- Set the router to compose HTML5 browser URLs.
- handle invalid routes with a wildcard route.
- navigate to the default route when the app launches with an empty path.

# Difference between forRoot and forChild
Only call RouterModule.forRoot in the root AppRoutingModule (or the AppModule if that's where you register top level application routes). In any other module, you must call the RouterModule.forChild method to register additional routes.


# Reference
- https://angular.io/guide/router
