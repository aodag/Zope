##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""Objects providing context for product initialization
"""
from AccessControl.PermissionRole import PermissionRole
import Globals, os, OFS.ObjectManager

class ProductContext:

    def __init__(self, product, app, package):
        self.__prod=product
        self.__app=app
        self.__pack=package

    def registerClass(self, instance_class=None, meta_type='', 
                      permission=None, constructors=(),
                      icon=None, permissions=None, legacy=(),
        ):
        """Register a constructor

        Keyword arguments are used to provide meta data:

        instance_class -- The class of the object that will be created.
        
          This is not currently used, but may be used in the future to
          increase object mobility.

        meta_type -- The kind of object being created
           This appears in add lists.  If not specified, then the class
           meta_type will be used.

        permission -- The permission name for the constructors.
           If not specified, then a permission name based on the
           meta type will be used.

        constructors -- A list of constructor methods
          A method can me a callable object with a __name__
          attribute giving the name the method should have in the
          product, or the method may be a tuple consisting of a
          name and a callable object.  The method must be picklable.

          The first method will be used as the initial method called
          when creating an object.

        icon -- The name of an image file in the package to
                be used for instances. Note that the class icon
                attribute will be set automagically if an icon is
                provided.

        permissions -- Additional permissions to be registered
           If not provided, then permissions defined in the
           class will be registered.
        
        legacy -- A list of legacy methods to be added to ObjectManager
                  for backward compatibility

        """
        app=self.__app
        initial=constructors[0]
        tt=type(())
        productObject=self.__prod

        if icon and instance_class is not None:
            setattr(instance_class, 'icon', 'Control_Panel/Products/%s/%s' %
                    (productObject.id, os.path.split(icon)[1]))

        OM=OFS.ObjectManager.ObjectManager

        perms={}
        for p in OM.__ac_permissions__: perms[p[0]]=None

        if permission is None:
            permission="Add %ss" % (meta_type or instance_class.meta_type)

        if permissions is None:
            permissions=[]
            if hasattr(instance_class, '__ac_permissions__'):
                for p in instance_class.__ac_permissions__:
                    if len(p) > 2: permissions.append((p[0],p[2]))
                    else: permissions.append(p[0])

        pr=None
        for p in (permission,)+tuple(permissions):
            if type(p) is tt: p, default= p
            else: default=('Manager',)

            if pr is None: pr=PermissionRole(p,default)
            
            if not perms.has_key(p):
                perms[p]=None
                OM.__ac_permissions__=OM.__ac_permissions__+((p,(),default),)

        for method in legacy:
            if type(method) is tt: name, method = method
            else: name=method.__name__
            if not OM.__dict__.has_key(name):
                setattr(OM, name, method)
                setattr(OM, name+'__roles__', pr)

        if type(initial) is tt: name, initial = initial
        else: name=initial.__name__

        if productObject.__dict__.has_key(name): return

        app._manage_add_product_meta_type(
            productObject, name, meta_type or instance_class.meta_type
            )
        
        setattr(productObject, name, initial)
        setattr(productObject, name+'__roles__', pr)

        for method in constructors[1:]:
            if type(method) is tt: name, method = method
            else: name=method.__name__
            if not productObject.__dict__.has_key(name):
                setattr(productObject, name, method)
                setattr(productObject, name+'__roles__', pr)

        if icon:
            name=os.path.split(icon)[1]
            icon=Globals.ImageFile(icon, self.__pack.__dict__)
            icon.__roles__=None
            setattr(productObject, name, icon)
            
