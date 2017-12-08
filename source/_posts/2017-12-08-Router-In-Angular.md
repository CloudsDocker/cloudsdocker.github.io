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

# Reference
- https://angular.io/guide/router
