# History

## 0.5.0 (2021-07-15)
This release contains changes for which you will need to update your code.

* Make the login step optional making it easier to access the test environment. Note: you will now need to manually call 
sedas.login() 

## 0.4.2 (2019-09-11)
* Add useragent header to stop the SeDAS firewall getting cross

## 0.4.1 (2019-07-30)
* Fix bulk download threads stopping on errors

## 0.4.0 (2019-07-12)
This release contains potentially backwards incompatible changes.

* Add source group lookup
* Add satellite lookup
* Make source group and satellite name optional on type specific searches
* Remove underscores from parameter names on all SeDASAPI functions (this may break existing code with named parameters)

## 0.3.0 (2019-07-11)
* Add Source Group search parameter
* Add Satellite Name search parameter

## 0.2.1 (2019-07-03)
* Documentation updates
* Download done queue added to bulk downloader

## 0.2.0 (2019-07-02)
* Initial release on PyPI

## 0.0.1 (2019-06-04)
* Initial code release without packaging